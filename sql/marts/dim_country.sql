-- dim_country: one row per country name in the seed (sql/seeds/country_region.csv).
-- market: 'UK' vs 'International' (the "channel" view in SPEC M2); 'Unknown' for
-- the source value 'Unspecified'. Region uses EU membership as of 2011.

create or replace table dim_country as
select
    cast(row_number() over (order by country_name) as integer) as country_key,
    country_name,
    nullif(iso_alpha2, '')                                     as iso_alpha2,
    region,
    market,
    country_name = 'United Kingdom'                            as is_domestic
from seed_country_region;
