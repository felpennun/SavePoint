#!/bin/sh
# Copies one local account (default: felipe) into the public Neon database under
# a new username and password, together with its profile, favourites, collection,
# status history, copies, lists and comments. Works that are not in the public
# subset are skipped. Runs inside the local db container; the Neon URL is read
# from /tmp/neon.url and the password hash from /tmp/clone.hash (both temporary).
#
# usage: clone_account_to_public.sh <local username> <new username>
set -eu

SRC_USER="${1:-felipe}"
NEW_USER="${2:-demo_user}"
LOCAL="psql -U savepoint_test -d savepoint_test -v ON_ERROR_STOP=1 -q"
NEON_URL="$(cat /tmp/neon.url)"
NEON="psql $NEON_URL -v ON_ERROR_STOP=1 -q"

SRC_ID=$($LOCAL -At -c "select id from auth_user where username='$SRC_USER'")
[ -n "$SRC_ID" ] || { echo "local user not found"; exit 1; }

stage() { # stage <table> <local SELECT> -- creates stg_<table> in Neon and fills it
  echo "== stage $1"
  $NEON -c "DROP TABLE IF EXISTS stg_$1; CREATE TABLE stg_$1 (LIKE $1);"
  $LOCAL -c "COPY ($2) TO STDOUT" | $NEON -c "COPY stg_$1 FROM STDIN"
}

stage accounts_accountprofile "select * from accounts_accountprofile where user_id=$SRC_ID"
stage accounts_favoriteslot "select * from accounts_favoriteslot where user_id=$SRC_ID"
stage library_libraryentry "select * from library_libraryentry where user_id=$SRC_ID"
stage library_statustransition "select t.* from library_statustransition t join library_libraryentry e on e.id=t.entry_id where e.user_id=$SRC_ID"
stage library_ownedcopy "select * from library_ownedcopy where user_id=$SRC_ID"
stage library_customlist "select * from library_customlist where user_id=$SRC_ID"
stage library_customlistitem "select i.* from library_customlistitem i join library_customlist l on l.id=i.list_id where l.user_id=$SRC_ID"
stage library_gamecomment "select * from library_gamecomment where user_id=$SRC_ID"

cols() { # cols <table> <exclude regex>: column list of the real Neon table
  $NEON -At -c "select string_agg(quote_ident(column_name), ',' order by ordinal_position) from information_schema.columns where table_schema='public' and table_name='$1' and column_name !~ '$2'"
}
list() { cols "$1" "$2" | tr ',' '\n' | sed "s/^user_id\$/:uid/; t; s/^/$3./" | paste -sd, -; }

HASH="$(cat /tmp/clone.hash)"
{
  echo "\\set ON_ERROR_STOP on"
  echo "BEGIN;"
  echo "INSERT INTO auth_user (password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)"
  echo "  VALUES ('$HASH', false, '$NEW_USER', '', '', '', false, true, now()) RETURNING id AS uid \\gset"

  echo "INSERT INTO accounts_accountprofile ($(cols accounts_accountprofile '^id$'))"
  echo "  SELECT $(list accounts_accountprofile '^id$' s) FROM stg_accounts_accountprofile s;"

  echo "INSERT INTO library_libraryentry ($(cols library_libraryentry '^id$'))"
  echo "  SELECT $(list library_libraryentry '^id$' s) FROM stg_library_libraryentry s WHERE s.work_id IN (SELECT id FROM catalogue_gamework);"

  echo "INSERT INTO accounts_favoriteslot ($(cols accounts_favoriteslot '^id$'))"
  echo "  SELECT $(list accounts_favoriteslot '^id$' s) FROM stg_accounts_favoriteslot s WHERE s.work_id IN (SELECT id FROM catalogue_gamework);"

  echo "INSERT INTO library_statustransition (from_status, to_status, changed_at, entry_id)"
  echo "  SELECT t.from_status, t.to_status, t.changed_at, ne.id FROM stg_library_statustransition t"
  echo "  JOIN stg_library_libraryentry oe ON oe.id = t.entry_id"
  echo "  JOIN library_libraryentry ne ON ne.user_id = :uid AND ne.work_id = oe.work_id;"

  echo "INSERT INTO library_ownedcopy ($(cols library_ownedcopy '^\$'))"
  echo "  SELECT $(list library_ownedcopy '^\$' s) FROM stg_library_ownedcopy s"
  echo "  WHERE s.work_id IN (SELECT id FROM catalogue_gamework) AND s.release_id IN (SELECT id FROM catalogue_gamerelease)"
  echo "    AND (s.edition_id IS NULL OR s.edition_id IN (SELECT id FROM catalogue_edition));"

  echo "INSERT INTO library_customlist ($(cols library_customlist '^\$'))"
  echo "  SELECT $(list library_customlist '^\$' s) FROM stg_library_customlist s;"

  echo "INSERT INTO library_customlistitem ($(cols library_customlistitem '^\$'))"
  echo "  SELECT $(list library_customlistitem '^\$' s) FROM stg_library_customlistitem s WHERE s.work_id IN (SELECT id FROM catalogue_gamework);"

  echo "INSERT INTO library_gamecomment ($(cols library_gamecomment '^\$'))"
  echo "  SELECT $(list library_gamecomment '^\$' s) FROM stg_library_gamecomment s WHERE s.work_id IN (SELECT id FROM catalogue_gamework);"

  echo "SELECT :uid AS new_user_id,"
  echo "  (SELECT count(*) FROM library_libraryentry WHERE user_id=:uid) AS entries,"
  echo "  (SELECT count(*) FROM stg_library_libraryentry) AS entries_in_source,"
  echo "  (SELECT count(*) FROM library_statustransition t JOIN library_libraryentry e ON e.id=t.entry_id WHERE e.user_id=:uid) AS transitions,"
  echo "  (SELECT count(*) FROM library_ownedcopy WHERE user_id=:uid) AS copies,"
  echo "  (SELECT count(*) FROM stg_library_ownedcopy) AS copies_in_source,"
  echo "  (SELECT count(*) FROM library_customlist WHERE user_id=:uid) AS lists,"
  echo "  (SELECT count(*) FROM library_customlistitem i JOIN library_customlist l ON l.id=i.list_id WHERE l.user_id=:uid) AS list_items,"
  echo "  (SELECT count(*) FROM stg_library_customlistitem) AS list_items_in_source,"
  echo "  (SELECT count(*) FROM library_gamecomment WHERE user_id=:uid) AS comments,"
  echo "  (SELECT count(*) FROM accounts_favoriteslot WHERE user_id=:uid) AS favorites;"
  echo "COMMIT;"
  echo "DROP TABLE stg_accounts_accountprofile, stg_accounts_favoriteslot, stg_library_libraryentry, stg_library_statustransition, stg_library_ownedcopy, stg_library_customlist, stg_library_customlistitem, stg_library_gamecomment;"
} > /tmp/clone.sql

psql "$NEON_URL" -x -q -f /tmp/clone.sql
rm -f /tmp/clone.sql /tmp/clone.hash
echo done
