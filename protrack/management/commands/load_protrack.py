import re, logging
from datetime import datetime, date, timedelta, time
from calendar import isleap

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from libazpm.contrib.chronologia.models import Service, Series, Season, Episode, Air
from protrack.db import Session
from protrack.db.static_query import airs_sql, safe_airs_sql, program_sql, description_sql, series_sql
from protrack.titlecase import titlecase

import warnings
warnings.filterwarnings("ignore") # protrack informix throws dumb _______ warnings we don't give a ____ about

logger = logging.getLogger('django_protrack')

def number_of_days(dt):
    """
    Returns the number of days in a given month
    """
    if dt.month is 2:
        if isleap(dt.year):
            return 29
        else:
            return 28
    elif dt.month is 4 or dt.month is 6 or dt.month is 9 or dt.month is 11:
        return 30
    else:
        return 31
        
def get_protrack_description(session, series, program, version, enc_type='utf8'):
    """
    get an episode or series description
    this is because of how protrack stores descriptions for everything in the same table
    a series is program = -1, version = -1, with a series id
    """
    params = {'series': series, 'program': program, 'version': version}
    results = session.execute(description_sql, params).fetchall()
    
    return u" ".join(unicode(row.pde_text, enc_type, errors='ignore') for row in results if row.pde_text != None)
    
def process_series(session, protrack_id):
    """
    process a series from Protrack with a description
    """
    try:
        series = Series.objects.using("default").get(protrack_id = protrack_id)
    except Series.DoesNotExist:
        series = Series()
    
    params = {'series': protrack_id}
    results = session.execute(series_sql, params).fetchone()    
    
    series.name = titlecase(re.sub('{[\w-]+}','',results.title)).replace("Bbc", "BBC").replace("Pbs","PBS")
    series.keyname = slugify(u"%s" % unicode(series.name,"utf8", errors="ignore"))
    series.protrack_id = protrack_id
    series.nola = results.nola
    series.description = get_protrack_description(session, protrack_id, -1, -1)
    
    series.save(using="default")
    
    return series

def process_season(session, series, season_number, total_shows, returns = True):
    """
    process a season
    this will always update a season instance and return it
    """
    try:
        season = Season.objects.using("default").get(number = int(season_number), series__protrack_id = series)
    except Season.DoesNotExist:
        season = Season()
        
    season.number = season_number
    season.total = total_shows
    season.series = process_series(session, series)
    
    season.save(using="default")
    
    if returns:
        return season
    else:
        return True #signifies success
    
def process_episode(session, row, duration):      
    """
    Process an episode updating descriptions if necessary, or creating a new one.
    
    Returns a valid instance of libazpm.contrib.protrack.models.Episode
    """
    try:
        episode = Episode.objects.using("default").select_related("season","series").get(protrack_id = row.version)
    except Episode.DoesNotExist:
        created = True
        episode = Episode()
    else:
        created = False
    
    if not created:
        #update the descriptions
        episode.short_description = unicode(row.short_description or "",'utf8')
        episode.description = get_protrack_description(session, row.series, row.program, row.version)
        #this triggers a process to update the series description
        season = process_season(session, row.series, episode.season.number, episode.season.total)

        if not episode.season_id:
            episode.season = season
        if not episode.series_id:
            episode.series = season.series
    else:
        #attach some basic wording to the episode
        episode.short_description = unicode(row.short_description or "",'utf8')
        episode.description = get_protrack_description(session, row.series, row.program, row.version)
        episode.protrack_id = row.version
        episode.duration = duration
        
        params = {'program': row.program}
        results = session.execute(program_sql, params).fetchone()
        
        #process the episode title, set it to nothing there isn't a title
        if str(results.title).upper() == "NONE" or results.title == None:
            episode.name = None
        else:
            episode.name = str(results.title).title().replace('Bbc', 'BBC').replace("Bbq","BBQ").replace("'S","'s").replace("'T","'t").strip()
        
        #slurp out the entire nola code for breaking it down
        full_nola_code = results.nola_code
        
        #before any nola processing, we should apply the nola to the episode
        episode.full_nola = full_nola_code
        
        #start working on numbers & season information
        episode.number = results.number
        
        #get the season information from the nola code
        season_number = "%s" % (full_nola_code[6:])
        
        #process the nola code for HD information and reset the season_number
        nola_code_modifier = None
        if len(season_number) > 6:
            nola_code_modifier = season_number[6:]
            season_number = season_number[0:6]
        
        if nola_code_modifier is 'H' or nola_code_modifier is 'Z':
            episode.high_definition = True
        else:
            episode.high_definition = False
        
        #when there is season information we must work on it
        if season_number is not "000000":
            if episode.number >= 100:
                season_number = season_number[0:(len(season_number)-3)]
            else:
                season_number = season_number[0:(len(season_number)-2)]
            
            season = process_season(session, row.series, int(season_number), results.total)
            
            episode.season = season
            episode.series = season.series
     
    #always save our work
    episode.save(using="default")
    return episode

class Command(BaseCommand):
    args = '<service_keyname service_keyname ...>'
    help = 'Load Schedule Data for given or all service'

    def handle(self, *args, **options):        
        services = []
        for keyname in args:
            try:
                service = Service.objects.using("default").get(keyname = keyname)
            except Service.DoesNotExist:
                raise CommandError('Service "%s" does not exist' % keyname)
            else:
                services.append(service)
                
        if not services:
            services = list(Service.objects.db_manager('default').protrack_services())
        
        if not services:
            raise CommandError('There are no services!')
        
        logger.info("Started protrack load for: {0:>s}".format(", ".join(service.name for service in services)))
        #date handling for today and arbritray date in future
        today = date.today()
        first_of_month = date(today.year, today.month, 1)
        last_of_month = date(today.year, today.month, number_of_days(today))
        two_weeks_ahead = timedelta(days = 14)
        two_weeks_ahead = today+two_weeks_ahead
        three_wks_ahead = timedelta(days = 21)
        three_wks_ahead = today+three_wks_ahead
        one_month_ahead = timedelta(days = 31)
        one_month_ahead = today+one_month_ahead
        
        # start a protrack session
        session = Session()
        
        services_processed = 0
        
        ct = ContentType.objects.get_for_model(Episode)

        with transaction.commit_on_success():
            if today != first_of_month:
                # if today is not the first of the month, delete everything from today forward
                logger.info("deleting all future airs for: {0:>s}".format(" ".join(t.keyname for t in services)))
                Air.objects.using("default").filter(service__in=services, date__gte=today).delete()


        for service in services:
            #special case where we have nothing in the DB for this month
            if not Air.objects.using("default").filter(service=service, date__range=(first_of_month, last_of_month)).exists():
                logger.info("no airs exist for %s in %d/%d" % (service.name, first_of_month.month, first_of_month.year))

                params = {'start': first_of_month, 'end': today, 'channel_key': service.protrack_key}
                results = session.execute(safe_airs_sql, params)
                counter = 0
                with transaction.commit_on_success():
                    for row in results.fetchall():
                        #process into timestamps
                        t = time(int(row.airtime[0:2]),int(row.airtime[3:5]),int(row.airtime[6:8]))
                        length = time(int(row.length[0:2]),int(row.length[3:5]),int(row.length[6:8]))
                        start = datetime.combine(row.airdate, t)
                        end = datetime.combine(row.airdate, t) + timedelta(hours=length.hour, minutes=length.minute, seconds=length.second)
                        #make episode
                        ep = process_episode(session, row, length)
                        #get/create the air
                        air, created = Air.objects.using("default").get_or_create(service = service, airing_type = ct, airing_id = ep.pk, date = row.airdate, duration = length, time = t, start = start, end = end)
                        counter += 1
                    else:
                        logger.info("found %d backlog airs for %s." % (counter, service.name))

            #regular case to get things into the future
            params = {'start': today, 'end': three_wks_ahead, 'channel_key': service.protrack_key}
            results = session.execute(airs_sql, params)
            counter = 0


            for row in results.fetchall():
                #process into timestamps
                t = time(int(row.airtime[0:2]),int(row.airtime[3:5]),int(row.airtime[6:8]))
                length = time(int(row.length[0:2]),int(row.length[3:5]),int(row.length[6:8]))
                start = datetime.combine(row.airdate, t)
                end = datetime.combine(row.airdate, t) + timedelta(hours=length.hour, minutes=length.minute, seconds=length.second)
                #process episode
                ep = process_episode(session, row, length)
                #get/create the air
                air, created = Air.objects.using("default").get_or_create(service = service, airing_type = ct, airing_id = ep.pk, date = row.airdate, duration = length, time = t, start = start, end = end)
                counter += 1
            else:
                logger.info("found %d airs for %s." % (counter, service.name))


            logger.info("finished processing %s." % service.name)
            services_processed += 1
            
        #end the protrack session                                    
        session.close()
        
        logger.info(u"Completed protrack load for: {0:>s}".format(" ".join(t.keyname for t in services)))

           