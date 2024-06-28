#!/bin/bash
set -e
 
echo [*] configuring $REPLICATION_ROLE instance
 
 # write in last line
echo "archive_mode = on" >> "$PGDATA/postgresql.conf"
echo "archive_command = 'mkdir -p /var/lib/postgresql/data/archivedir && test ! -f /var/lib/postgresql/data/archivedir/%f && cp %p /var/lib/postgresql/data/archivedir/%f'" >> "$PGDATA/postgresql.conf"
echo "max_connections = $MAX_CONNECTIONS" >> "$PGDATA/postgresql.conf"
echo "default_transaction_read_only = off" >> "$PGDATA/postgresql.conf"
 
# We set master replication-related parameters for both slave and master,
# so that the slave might work as a primary after failover.
echo "wal_level = hot_standby" >> "$PGDATA/postgresql.conf"
echo "max_wal_senders = $MAX_WAL_SENDERS" >> "$PGDATA/postgresql.conf"

# slave settings, ignored on master
echo "hot_standby = on" >> "$PGDATA/postgresql.conf"
echo "host replication $REPLICATION_USER 0.0.0.0/0 trust" >> "$PGDATA/pg_hba.conf"