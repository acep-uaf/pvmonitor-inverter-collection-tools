-- Individually defined meter types with all the individual credentials
CREATE TABLE meters (
	meterID		INTEGER PRIMARY KEY,
	meterClass	TEXT,
	meterType	TEXT,
	credCode	TEXT,
	meterUsername	TEXT,
	meterPassword	TEXT
);

-- Table for data locations for reading
-- and writing data to the bmon server
CREATE TABLE dataLocations (
	urlID		INTEGER PRIMARY KEY,
	dataMode	TEXT,
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

-- Some installations have multiple independently reporting
-- physical installations that do not record on the same
-- time axis.
CREATE TABLE installUnits (
	siteName	TEXT,
	siteUnit	TEXT,
	unitName	TEXT
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


