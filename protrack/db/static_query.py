airs_sql = """
select
a.ai_ser_id as series,  
a.ai_prog_id as program,  a.ai_vsn_id as version, 
a.ai_air_date as airdate, a.ai_air_time as airtime, 
a.ai_air_len as length, p.pgu_text as short_description
from air13 a, outer proguide p 
where a.ai_air_date >= :start 
and a.ai_air_date <= :end 
and a.ai_virt_chnl = :channel_key
and p.pgu_ser_id = a.ai_ser_id
and p.pgu_sea_id = a.ai_sea_id 
and p.pgu_prog_id = a.ai_prog_id 
and p.pgu_vsn_id = a.ai_vsn_id 
group by ai_ser_id, ai_prog_id, ai_vsn_id, ai_air_date, ai_air_time, ai_air_len, pgu_text
order by a.ai_air_date asc
"""

safe_airs_sql = """
select
a.ai_ser_id as series,  
a.ai_prog_id as program,  a.ai_vsn_id as version, 
a.ai_air_date as airdate, a.ai_air_time as airtime, 
a.ai_air_len as length, p.pgu_text as short_description
from safeair13 a, outer proguide p 
where a.ai_air_date >= :start 
and a.ai_air_date <= :end 
and a.ai_virt_chnl = :channel_key
and p.pgu_ser_id = a.ai_ser_id
and p.pgu_sea_id = a.ai_sea_id 
and p.pgu_prog_id = a.ai_prog_id 
and p.pgu_vsn_id = a.ai_vsn_id 
group by ai_ser_id, ai_prog_id, ai_vsn_id, ai_air_date, ai_air_time, ai_air_len, pgu_text
order by a.ai_air_date asc
"""

program_sql = """
select distinct
vsn_nola_code as nola_code, vsn_order as number, vsn_total as total, pg_title as title
from quad_tab
where pg_serial = :program
"""

description_sql = """
select pde_text,  pde_disp_ord
from progdesc 
where pde_ser_id = :series
and pde_prog_id = :program
and pde_vsn_id = :version
and pde_text is not null
order by pde_disp_ord asc
"""

series_sql = """
select ser_nola_base as nola, ser_title as title
from quad_tab
where ser_serial = :series
"""