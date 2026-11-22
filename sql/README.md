# Legacy database fixture

[`chuxin.fixture.sql`](chuxin.fixture.sql) preserves the historical MySQL schema: 19 tables, a `public_profiles` view, four synthetic accounts and linked profiles, and an already-used synthetic doctor verification code. The fixture accounts cannot log in.

Use MySQL 8.4 and a new, empty local schema. The script does not select a database or drop any tables:

```sh
mysql --host=127.0.0.1 --user=fixture_operator --password \
  --database=chuxin_legacy_fixture < sql/chuxin.fixture.sql
```

This fixture is for legacy schema inspection and import testing, not for initializing the current app. For a current local environment, use the backend's Flyway migrations and the [scale library recovery guide](../RECOVERY.md). The original dump and existing account hashes are not required for either workflow.
