-- Schema exactly as created by v0.4.0 (SQLModel create_all, before Alembic). v0.2.0 = the same without climatecache.
CREATE TABLE user (
	id INTEGER NOT NULL, 
	username VARCHAR NOT NULL, 
	password_hash VARCHAR NOT NULL, 
	display_name VARCHAR NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_user_username ON user (username);
CREATE TABLE garden (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	name VARCHAR NOT NULL, 
	latitude FLOAT NOT NULL, 
	longitude FLOAT NOT NULL, 
	postal_code VARCHAR NOT NULL, 
	frost_probability INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE
);
CREATE TABLE climatecache (
	garden_id INTEGER NOT NULL, 
	latitude FLOAT NOT NULL, 
	longitude FLOAT NOT NULL, 
	summary JSON NOT NULL, 
	fetched_at DATETIME NOT NULL, 
	PRIMARY KEY (garden_id), 
	FOREIGN KEY(garden_id) REFERENCES garden (id) ON DELETE CASCADE
);
