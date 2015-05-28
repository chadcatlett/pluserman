PRAGMA foreign_keys = false;

-- ----------------------------
--  Table structure for "group"
-- ----------------------------
DROP TABLE IF EXISTS "group";
CREATE TABLE "group" (
 "id" INTEGER NOT NULL PRIMARY KEY,
 "name" VARCHAR(255) NOT NULL
);

-- ----------------------------
--  Records of "main"."group"
-- ----------------------------
BEGIN;
INSERT INTO "group" VALUES (3, 'restricted');
INSERT INTO "group" VALUES (2, 'users');
INSERT INTO "group" VALUES (1, 'wheel');
COMMIT;

-- ----------------------------
--  Table structure for "group_membership"
-- ----------------------------
DROP TABLE IF EXISTS "group_membership";
CREATE TABLE "group_membership" (
 "id" INTEGER NOT NULL PRIMARY KEY,
 "group_id" INTEGER NOT NULL,
 "user_id" INTEGER NOT NULL,
 FOREIGN KEY ("group_id") REFERENCES "group" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
 FOREIGN KEY ("user_id") REFERENCES "user" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- ----------------------------
--  Records of "main"."group_membership"
-- ----------------------------
BEGIN;
INSERT INTO "group_membership" VALUES (1, 1, 1);
INSERT INTO "group_membership" VALUES (2, 2, 1);
INSERT INTO "group_membership" VALUES (3, 2, 2);
INSERT INTO "group_membership" VALUES (4, 3, 2);
COMMIT;

-- ----------------------------
--  Table structure for "user"
-- ----------------------------
DROP TABLE IF EXISTS "user";
CREATE TABLE "user" (
 "id" INTEGER NOT NULL PRIMARY KEY,
 "userid" VARCHAR(255) NOT NULL,
 "first_name" VARCHAR(255) NOT NULL,
 "last_name" VARCHAR(255) NOT NULL
);

-- ----------------------------
--  Records of "main"."user"
-- ----------------------------
BEGIN;
INSERT INTO "user" VALUES (1, 'admin', 'Mighty', 'Admin');
INSERT INTO "user" VALUES (2, 'user1', 'Humble', 'User1');
INSERT INTO "user" VALUES (3, "lonely", "No", "Group");
COMMIT;

-- ----------------------------
--  Indexes structure for table "group"
-- ----------------------------
CREATE UNIQUE INDEX "group_name" ON "group" ("name");

-- ----------------------------
--  Indexes structure for table "group_membership"
-- ----------------------------
CREATE INDEX "group_membership_group_id" ON "group_membership" ("group_id");
CREATE UNIQUE INDEX "group_membership_group_id_user_id" ON "group_membership" ("group_id", "user_id");
CREATE INDEX "group_membership_user_id" ON "group_membership" ("user_id");

-- ----------------------------
--  Indexes structure for table "user"
-- ----------------------------
CREATE UNIQUE INDEX "user_userid" ON "user" ("userid");

PRAGMA foreign_keys = true;
