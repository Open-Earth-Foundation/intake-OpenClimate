'''
Script to query OpenClimate database and save output

Directory tree:
.
├── actors_<type>.csv
├── emissions_<dataset>_<actor>.csv
└── ndc_iges_all.csv
'''
import os
from os.path import join
from os.path import dirname
import pandas as pd
from pathlib import Path
import psycopg2
from sshtunnel import SSHTunnelForwarder
import textwrap

def read_config(dotrc: str=None, sep: str='='):
    '''read configuration file
    dotrc [str]: input file (default '~/.oc_db_params')
    sep: seperator [default: '=']
    '''
    dotrc = dotrc or './.env'
    path = Path(dotrc).expanduser()

    keys = [
        'ssh_username',
        'ssh_pkey',
        'remote_ip',
        'db_uri',    
        'dbname',    
        'user',    
        'password',    
        'host'
    ]

    if path.is_file():
        with open(path) as file:
            config = {line.strip().split(sep, 1)[0] : line.strip().split(sep, 1)[1].strip() 
                      for line in file.readlines() if sep in line}

        if not set(keys).issubset(config.keys()):
            missing_keys = set(keys) - set(config.keys())
            print(f"{missing_keys} not defined in {path.as_posix()}")

    return config

def query_database(query: str=None, 
                   remote_ip: str=None, 
                   ssh_username: str=None, 
                   ssh_pkey: str=None, 
                   db_uri: str=None, 
                   dbname: str=None, 
                   user: str=None, 
                   password: str=None, 
                   host: str=None, 
                   output_file: str=None) -> None:
            
    # ports
    ssh_port = 22
    postgres_port = 5432
    
    try:
        with SSHTunnelForwarder(
            (remote_ip, ssh_port), 
            ssh_username=ssh_username, 
            ssh_pkey=ssh_pkey,
            remote_bind_address=(db_uri, postgres_port)) as server: 

            # database parameters
            params = {
                'dbname': dbname,
                'user': user,
                'password': password,
                'host': host,
                'port': server.local_bind_port
            }
            
            # connect to database and open a cursor
            with psycopg2.connect(**params) as conn:
                with conn.cursor() as curs: 
                    if Path(query).is_file():
                        with open(query, 'r') as f: 
                            query = f.read()

                    df = pd.read_sql_query(query, conn)
                    
                    return df
    except:
        print("Connection failed")
        

if __name__ == "__main__": 
    # environment vars
    dotenv_path = join(dirname(__file__), '.env') 
    args = read_config(dotenv_path)
    
    # output types 
    to_csv = True
    to_parquet = False
    
    # output directory
    dir_out = './data/'
    dir_out = Path(dir_out).expanduser().absolute()
    dir_out.mkdir(parents=True, exist_ok=True)
    
    # output file
    output_file=None
    
    # get NDCs
    query = '''
        SELECT
            tar.actor_id AS actor,
            tar.target_type,
            tar.baseline_year,
            tar.target_year,
            tar.target_value,
            tar.target_unit,
            tar."URL"
        FROM "Target" AS tar
        WHERE tar.datasource_id LIKE '%IGES_NDC%';
    '''

    query = textwrap.dedent(query)

    df_ndc = query_database(query=query, **args)
    
    if to_parquet:
        df_ndc.to_parquet(f'{dir_out}/ndc_iges_all.parquet', index=False, compression='gzip')
        
    if to_csv:
        df_ndc.to_csv(f'{dir_out}/ndc_iges_all.csv', index=False)
        
    # partition into actors
    for actor in df_ndc['actor']:
        df_tmp = df_ndc.loc[df_ndc['actor'] == actor]
        
        if to_parquet:
            df_tmp.to_parquet(f'{dir_out}/ndc_iges_{actor}.parquet', index=False, compression='gzip')
            
        if to_csv:
            df_tmp.to_csv(f'{dir_out}/ndc_iges_{actor}.csv', index=False)


    # get countries
    query = '''SELECT actor_id AS actor, name FROM "Actor" WHERE type='country';'''
    df_country = query_database(query=query, **args, output_file=output_file)
    
    if to_parquet:
        df_country.to_parquet(f'{dir_out}/actors_country.parquet', index=False, compression='gzip')
        
    if to_csv:
        df_country.to_csv(f'{dir_out}/actors_country.csv', index=False)
    
    # get subnationals
    query = '''SELECT actor_id AS actor, name, type, is_part_of FROM "Actor" WHERE type LIKE 'adm%';'''
    df_subnat = query_database(query=query, **args, output_file=output_file)
    
    if to_parquet:
        df_subnat.to_parquet(f'{dir_out}/actors_subnat.parquet', index=False, compression='gzip')
        
    if to_csv:
        df_subnat.to_csv(f'{dir_out}/actors_subnat.csv', index=False)
    
    # get datasets
    query = '''
    SELECT DISTINCT
        e.datasource_id,
        LOWER(SUBSTRING(e.datasource_id, 0, STRPOS(e.datasource_id, ':'))) AS dataset
    FROM "EmissionsAgg" AS e
    JOIN "Actor" AS a
    ON e.actor_id=a.actor_id
    WHERE a.type='country';
    '''
    
    df_dataset = query_database(query=query, **args, output_file=output_file)
        
    # loop over datasets, extract country and save
    for datasource, dataset in zip(df_dataset['datasource_id'], df_dataset['dataset']):
        query = '''
            SELECT
                e.actor_id AS actor,
                e.year,
                e.total_emissions AS emissions
            FROM "EmissionsAgg" AS e
            WHERE e.datasource_id='{0}'
            ;
            '''.format(datasource)

        query = textwrap.dedent(query)
        
        df = query_database(query=query, **args)
        
        # apply aggregate functions
        df_agg = (
            df
            .sort_values('year')
            .groupby('actor')['emissions']
            .agg(['cumsum', 'diff', 'pct_change'])
            .rename(columns={'cumsum': 'cumulative_emissions', 
                            'diff': 'first_difference', 
                            'pct_change': 'percent_change_as_decimal'})
        )

        df = df.join(df_agg)
        
        if to_parquet:
            df.to_parquet(f'{dir_out}/emissions_{dataset}_all.parquet', index=False, compression='gzip')
            
        if to_csv:
            df.to_csv(f'{dir_out}/emissions_{dataset}_all.csv', index=False)
        
        # loop over actors
        for actor in set(df['actor']):
            df_tmp = df.loc[df['actor'] == actor]
            
            if to_parquet:
                df_tmp.to_parquet(f'{dir_out}/emissions_{dataset}_{actor}.parquet', index=False, compression='gzip')

            if to_csv:
                df_tmp.to_csv(f'{dir_out}/emissions_{dataset}_{actor}.csv', index=False)
                
    # subnational datasets
    datasources = ['EPA:state_GHG_inventory:2022-08-31', 'ECCC:GHG_inventory:2022-04-13']
    for datasource in datasources:
        dataset = datasource.split(':')[0].lower()
        query = '''
            SELECT
                e.actor_id AS actor,
                e.year,
                e.total_emissions AS emissions
            FROM "EmissionsAgg" AS e
            WHERE e.datasource_id='{0}'
            ;
            '''.format(datasource)

        query = textwrap.dedent(query)
        
        df = query_database(query=query, **args)
        
        df_agg = (
            df
            .sort_values('year')
            .groupby('actor')['emissions']
            .agg(['cumsum', 'diff', 'pct_change'])
            .rename(columns={'cumsum': 'cumulative_emissions', 
                            'diff': 'first_difference', 
                            'pct_change': 'percent_change_as_decimal'})
        )

        df = df.join(df_agg)
        
        if to_parquet:
            df.to_parquet(f'{dir_out}/emissions_{dataset}_all.parquet', index=False, compression='gzip')
        
        if to_csv:
            df.to_csv(f'{dir_out}/emissions_{dataset}_all.csv', index=False)
        
        # loop over actors
        for actor in set(df['actor']):
            df_tmp = df.loc[df['actor'] == actor]
            
            if to_parquet:
                df_tmp.to_parquet(f'{dir_out}/emissions_{dataset}_{actor}.parquet', index=False, compression='gzip')
            
            if to_csv:
                df_tmp.to_csv(f'{dir_out}/emissions_{dataset}_{actor}.csv', index=False)
                     
        actor_agg = actor.split('-')[0]
        
        # aggregate
        df_sum = df[['year','emissions']].groupby(by=['year']).sum().reset_index()

        # apply aggregate functions
        df_agg = (
            df_sum['emissions']
            .agg(['cumsum', 'diff', 'pct_change'])
            .rename(columns={'cumsum': 'cumulative_emissions', 
                            'diff': 'first_difference', 
                            'pct_change': 'percent_change_as_decimal'})
        )

        df_sum = df_sum.join(df_agg)
        
        if to_parquet:
            df_sum.to_parquet(f'{dir_out}/emissions_{dataset}_{actor_agg}.parquet', index=False, compression='gzip')
        
        if to_csv:
            df_sum.to_csv(f'{dir_out}/emissions_{dataset}_{actor_agg}.csv', index=False)
        