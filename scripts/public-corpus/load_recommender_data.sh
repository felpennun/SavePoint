#!/bin/sh
# Copies the recommender inputs built by export_recommender_data.sql into Neon.
# Runs inside the local db container; the Neon URL is read from /tmp/neon.url.
set -eu

LOCAL="psql -U savepoint_test -d savepoint_test -v ON_ERROR_STOP=1 -q"
NEON="psql $(cat /tmp/neon.url) -v ON_ERROR_STOP=1 -q"

copy_table() { # copy_table <pubexport table> <neon table>
  c=$($LOCAL -At -c "select string_agg(quote_ident(column_name), ',' order by ordinal_position) from information_schema.columns where table_schema='pubexport' and table_name='$1'")
  echo "== $1 -> $2"
  $LOCAL -c "COPY (SELECT $c FROM pubexport.$1) TO STDOUT" | $NEON -c "COPY $2 ($c) FROM STDIN"
}

copy_table workfeaturevector recommendations_workfeaturevector
copy_table corpusratingsnapshot catalogue_corpusratingsnapshot
copy_table corpuspopularitysnapshot catalogue_corpuspopularitysnapshot
echo done
