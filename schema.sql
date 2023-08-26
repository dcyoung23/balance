CREATE TABLE 'balance' 
('user_id' INTEGER PRIMARY KEY NOT NULL
, 'current' NUMERIC NOT NULL DEFAULT 0 
, 'available' NUMERIC NOT NULL DEFAULT 0 )

CREATE TABLE 'frequency' 
('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
, 'frequency' TEXT
, 'modifier' TEXT
, 'n' INTEGER)

CREATE TABLE 'schedule' 
('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
, 'name' TEXT NOT NULL
, 'type_id' INTEGER NOT NULL
, 'current_dt' DATETIME
, 'snoozed_dt' DATETIME
, 'previous_dt' DATETIME
, 'completed_dt' DATETIME
,'frequency_id' INTEGER
, 'repeat' INTEGER DEFAULT 1 
, 'amount' NUMERIC
, 'user_id' INTEGER
, 'pmt_source' TEXT
, 'pmt_method' TEXT)

CREATE TABLE 'type' 
('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
, 'label' TEXT NOT NULL
, 'factor' INTEGER)

CREATE TABLE 'users' 
('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
, 'username' TEXT
, 'hash' TEXT)

CREATE INDEX 'user_id' ON "schedule" ("user_id")

CREATE TABLE 'cd'
('cd' TEXT PRIMARY KEY
, 'cd_group' TEXT
, 'cd_desc' TEXT)