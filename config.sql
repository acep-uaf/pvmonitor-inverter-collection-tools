-- Individually defined meter types with all the individual credentials
CREATE TABLE meters (
	meterID		INTEGER PRIMARY KEY,
	meterClass	TEXT,
	meterType	TEXT,
	credCode	TEXT,
	meterUsername	TEXT,
	meterPassword	TEXT
);

-- Table for data locations
CREATE TABLE dataLocations (
	urlID		INTEGER PRIMARY KEY,
	urlCode		TEXT,
	urlTemplate	TEXT
);

-- meterID is foreignKey to meters.meterID to match up with credCode
-- meterID when initialized will not be set, python code will systematically
-- populate this column.
-- siteEnabled: enum
--   0 : off
--   1 : collect data
--   9 : debug; show data; do not post
CREATE TABLE installations (
	installID	INTEGER PRIMARY KEY,
	meterID 	INTEGER,
	siteName	TEXT,
	siteCode	TEXT,
	credCode	TEXT,
	urlCode		TEXT,
	dataStoreKey	TEXT,
	dataUnits	TEXT,
	siteEnabled	INTEGER
);

-- Basic statistics for site installations
CREATE TABLE siteStatus (
	installID	INTEGER,
	lastAttempt	DATETIME,
	lastSuccess	DATETIME,
	lastRuntime	INTEGER,
	errorMessage	TEXT,
	debugMessage	TEXT
);


