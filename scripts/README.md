# Query OpenClimate Database

These scripts are used to query the [OpenClimate](https://openclimate.network/) database.
`query_script.py` does all the work, it performs the queries and saved the output to `./data/`

Run the command like this:
```python
python ./query_script.py
```

This requires the proper credentials stored in `./.env`.

One the database is queried. Push all the files in `./data` to [IPFS](https://ipfs.tech/) via [web3.storage](https://web3.storage/):

```sh
w3 put --no-wrap --name intake_openclimate_files_v1 ./data/
```

This requires an account withe [web3.storage](https://web3.storage/).