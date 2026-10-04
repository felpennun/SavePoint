-- Public deployment subset: governed works with an IGDB rating or a PopScore > 0
-- (plus the DLC children their detail pages list). Built in a scratch schema.
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

CREATE TABLE pubexport.related AS
SELECT r.* FROM catalogue_relatedcontent r JOIN pubexport.core c ON c.id = r.parent_work_id;

-- every work that is exported: the core plus the children of the related content
CREATE TABLE pubexport.works_all AS
SELECT id FROM pubexport.core
UNION
SELECT child_work_id FROM pubexport.related;
ALTER TABLE pubexport.works_all ADD PRIMARY KEY (id);

CREATE TABLE pubexport.gamework AS
SELECT g.* FROM catalogue_gamework g JOIN pubexport.works_all w ON w.id = g.id;

CREATE TABLE pubexport.gamerelease AS
SELECT r.* FROM catalogue_gamerelease r JOIN pubexport.works_all w ON w.id = r.work_id;
CREATE TABLE pubexport.platform AS
SELECT p.* FROM catalogue_platform p WHERE p.id IN (SELECT platform_id FROM pubexport.gamerelease);

CREATE TABLE pubexport.gamealias AS
SELECT a.* FROM catalogue_gamealias a JOIN pubexport.core w ON w.id = a.work_id;
CREATE TABLE pubexport.assetattribution AS
SELECT a.* FROM catalogue_assetattribution a JOIN pubexport.works_all w ON w.id = a.work_id;
CREATE TABLE pubexport.sourcerecord AS
SELECT a.* FROM catalogue_sourcerecord a JOIN pubexport.works_all w ON w.id = a.work_id;
CREATE TABLE pubexport.corpuspopularityscore AS
SELECT a.* FROM catalogue_corpuspopularityscore a JOIN pubexport.works_all w ON w.id = a.work_id
WHERE a.corpus_version = '2026.09.2';

CREATE TABLE pubexport.gamework_genres AS SELECT m.* FROM catalogue_gamework_genres m JOIN pubexport.works_all w ON w.id = m.gamework_id;
CREATE TABLE pubexport.gamework_franchises AS SELECT m.* FROM catalogue_gamework_franchises m JOIN pubexport.works_all w ON w.id = m.gamework_id;
CREATE TABLE pubexport.gamework_developers AS SELECT m.* FROM catalogue_gamework_developers m JOIN pubexport.works_all w ON w.id = m.gamework_id;
CREATE TABLE pubexport.gamework_publishers AS SELECT m.* FROM catalogue_gamework_publishers m JOIN pubexport.works_all w ON w.id = m.gamework_id;
CREATE TABLE pubexport.gamework_themes AS SELECT m.* FROM catalogue_gamework_themes m JOIN pubexport.works_all w ON w.id = m.gamework_id;
CREATE TABLE pubexport.gamework_player_perspectives AS SELECT m.* FROM catalogue_gamework_player_perspectives m JOIN pubexport.works_all w ON w.id = m.gamework_id;
CREATE TABLE pubexport.gamework_game_modes AS SELECT m.* FROM catalogue_gamework_game_modes m JOIN pubexport.works_all w ON w.id = m.gamework_id;
CREATE TABLE pubexport.gamework_subgenres AS SELECT m.* FROM catalogue_gamework_subgenres m JOIN pubexport.works_all w ON w.id = m.gamework_id;
CREATE TABLE pubexport.gameworkcuratedlabel AS SELECT m.* FROM catalogue_gameworkcuratedlabel m JOIN pubexport.works_all w ON w.id = m.work_id;

CREATE TABLE pubexport.genre AS SELECT * FROM catalogue_genre;
CREATE TABLE pubexport.theme AS SELECT * FROM catalogue_theme;
CREATE TABLE pubexport.playerperspective AS SELECT * FROM catalogue_playerperspective;
CREATE TABLE pubexport.gamemode AS SELECT * FROM catalogue_gamemode;
CREATE TABLE pubexport.subgenre AS SELECT * FROM catalogue_subgenre;
CREATE TABLE pubexport.curatedlabel AS SELECT * FROM catalogue_curatedlabel;
CREATE TABLE pubexport.franchise AS SELECT * FROM catalogue_franchise WHERE id IN (SELECT franchise_id FROM pubexport.gamework_franchises);
CREATE TABLE pubexport.developer AS SELECT * FROM catalogue_developer WHERE id IN (SELECT developer_id FROM pubexport.gamework_developers);
CREATE TABLE pubexport.publisher AS SELECT * FROM catalogue_publisher WHERE id IN (SELECT publisher_id FROM pubexport.gamework_publishers);
CREATE TABLE pubexport.corpusversion AS SELECT * FROM catalogue_corpusversion;

SELECT 'core' t, count(*) FROM pubexport.core
UNION ALL SELECT 'works_all', count(*) FROM pubexport.works_all
UNION ALL SELECT 'related', count(*) FROM pubexport.related
UNION ALL SELECT 'release', count(*) FROM pubexport.gamerelease
UNION ALL SELECT 'platform', count(*) FROM pubexport.platform
UNION ALL SELECT 'alias', count(*) FROM pubexport.gamealias
UNION ALL SELECT 'asset', count(*) FROM pubexport.assetattribution
UNION ALL SELECT 'source', count(*) FROM pubexport.sourcerecord
UNION ALL SELECT 'popscore', count(*) FROM pubexport.corpuspopularityscore
UNION ALL SELECT 'curatedlabel_ev', count(*) FROM pubexport.gameworkcuratedlabel
UNION ALL SELECT 'developer', count(*) FROM pubexport.developer
UNION ALL SELECT 'franchise', count(*) FROM pubexport.franchise
UNION ALL SELECT 'publisher', count(*) FROM pubexport.publisher
UNION ALL SELECT 'size_MB', (sum(pg_total_relation_size(c.oid))/1048576)::bigint
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'pubexport' AND c.relkind = 'r';
