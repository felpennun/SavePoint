#!/bin/sh
# Copies the pubexport schema of the local database into Neon (public schema).
# Runs inside the local db container; the Neon URL is read from /tmp/neon.url.
set -eu

LOCAL="psql -U savepoint_test -d savepoint_test -v ON_ERROR_STOP=1 -q"
NEON="psql $(cat /tmp/neon.url) -v ON_ERROR_STOP=1 -q"

cols() { # cols <pubexport table>
  $LOCAL -At -c "select string_agg(quote_ident(column_name), ',' order by ordinal_position) from information_schema.columns where table_schema='pubexport' and table_name='$1'"
}

copy_table() { # copy_table <pubexport table> <neon table>
  c=$(cols "$1")
  echo "== $1 -> $2"
  $LOCAL -c "COPY (SELECT $c FROM pubexport.$1) TO STDOUT" | $NEON -c "COPY $2 ($c) FROM STDIN"
}

echo "== staging platform and release"
$NEON -c "DROP TABLE IF EXISTS stg_release, stg_platform;
          CREATE TABLE stg_platform (LIKE catalogue_platform);
          CREATE TABLE stg_release (LIKE catalogue_gamerelease);"
copy_table platform stg_platform
copy_table gamerelease stg_release

echo "== platform conflicts (same slug, different name)"
$NEON -c "DO \$\$ BEGIN
  IF EXISTS (SELECT 1 FROM stg_platform s JOIN catalogue_platform p ON p.slug = s.slug AND p.name <> s.name) THEN
    RAISE EXCEPTION 'platform slug conflict';
  END IF;
END \$\$;
INSERT INTO catalogue_platform SELECT s.* FROM stg_platform s
  WHERE NOT EXISTS (SELECT 1 FROM catalogue_platform p WHERE p.name = s.name);"

for t in genre theme playerperspective gamemode subgenre curatedlabel franchise developer; do
  copy_table "$t" "catalogue_$t"
done

copy_table gamework catalogue_gamework
copy_table gamealias catalogue_gamealias
copy_table assetattribution catalogue_assetattribution
copy_table sourcerecord catalogue_sourcerecord
copy_table related catalogue_relatedcontent
copy_table corpuspopularityscore catalogue_corpuspopularityscore
copy_table gamework_genres catalogue_gamework_genres
copy_table gamework_franchises catalogue_gamework_franchises
copy_table gamework_developers catalogue_gamework_developers
copy_table gamework_themes catalogue_gamework_themes
copy_table gamework_player_perspectives catalogue_gamework_player_perspectives
copy_table gamework_game_modes catalogue_gamework_game_modes
copy_table gamework_subgenres catalogue_gamework_subgenres
copy_table gameworkcuratedlabel catalogue_gameworkcuratedlabel

echo "== releases with the platform ids that exist in Neon"
rcols=$(cols gamerelease)
rc=$(echo "r.$rcols" | sed 's/,/,r./g; s/r\.platform_id/p.id/')
$NEON -c "INSERT INTO catalogue_gamerelease ($rcols)
  SELECT $rc FROM stg_release r
  JOIN stg_platform s ON s.id = r.platform_id
  JOIN catalogue_platform p ON p.name = s.name;
  DROP TABLE stg_release, stg_platform;"

echo "== corpus version"
$NEON -c "INSERT INTO catalogue_corpusversion (version, ruleset_sha256, created_at, is_active, governed_count)
  VALUES ('2026.09.2', '28ff0ac107bddb2d36faf38732c1040a2052853d33514dbee146389bd0079144', '2026-09-09 02:45:02.421199+00', false, 190479)
  ON CONFLICT (version) DO NOTHING;"
echo done
