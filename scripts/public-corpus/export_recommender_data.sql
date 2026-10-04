-- Recommender inputs for the public subset: current feature vectors plus the
-- frozen rating/popularity snapshots of the active corpus version.
DROP SCHEMA IF EXISTS pubexport CASCADE;
CREATE SCHEMA pubexport;

CREATE TABLE pubexport.core AS
SELECT g.id
FROM catalogue_gamework g
WHERE g.in_corpus AND NOT g.is_dlc
  AND (g.total_rating IS NOT NULL OR g.rating IS NOT NULL
       OR EXISTS (SELECT 1 FROM catalogue_corpuspopularityscore s
                  WHERE s.work_id = g.id AND s.corpus_version = '2026.09.2' AND s.score > 0));
ALTER TABLE pubexport.core ADD PRIMARY KEY (id);

CREATE TABLE pubexport.workfeaturevector AS
SELECT v.* FROM recommendations_workfeaturevector v JOIN pubexport.core c ON c.id = v.work_id
WHERE v.feature_set_version = 'fs-v13-family-weighted-tags';
CREATE TABLE pubexport.corpusratingsnapshot AS
SELECT s.* FROM catalogue_corpusratingsnapshot s JOIN pubexport.core c ON c.id = s.work_id
WHERE s.corpus_version = '2026.09.2';
CREATE TABLE pubexport.corpuspopularitysnapshot AS
SELECT s.* FROM catalogue_corpuspopularitysnapshot s JOIN pubexport.core c ON c.id = s.work_id
WHERE s.corpus_version = '2026.09.2';

SELECT 'vectors' t, count(*) FROM pubexport.workfeaturevector
UNION ALL SELECT 'ratingsnap', count(*) FROM pubexport.corpusratingsnapshot
UNION ALL SELECT 'popsnap', count(*) FROM pubexport.corpuspopularitysnapshot
UNION ALL SELECT 'size_MB', (sum(pg_total_relation_size(c.oid))/1048576)::bigint
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'pubexport' AND c.relkind = 'r';
