-- Fred the Fish / Project 3a — Azure SQL Database (T-SQL)
-- Matches JPA entity: com.cs506.project3a.Player (@Table name = "players")
--
-- Create the database in Azure Portal (or Azure CLI) first, then run this script
-- connected to that database (Query Editor, sqlcmd, SSMS, Azure Data Studio).
--
-- Spring Boot (replace MySQL driver with com.microsoft.sqlserver:mssql-jdbc):
--   SPRING_DATASOURCE_URL=jdbc:sqlserver://<server>.database.windows.net:1433;database=project3a_db;encrypt=true;trustServerCertificate=false;hostNameInCertificate=*.database.windows.net;loginTimeout=30;
--   SPRING_DATASOURCE_USERNAME=<sql-admin-user>
--   SPRING_DATASOURCE_PASSWORD=<password>
--   SPRING_DATASOURCE_DRIVER_CLASS_NAME=com.microsoft.sqlserver.jdbc.SQLServerDriver
--   SPRING_JPA_HIBERNATE_DDL_AUTO=update

-- ---------------------------------------------------------------------------
-- Table: players
-- ---------------------------------------------------------------------------
IF OBJECT_ID(N'dbo.players', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.players (
        id         BIGINT        IDENTITY(1,1) NOT NULL,
        username   NVARCHAR(255) NOT NULL,
        password   NVARCHAR(255) NOT NULL,
        high_score INT           NOT NULL
            CONSTRAINT DF_players_high_score DEFAULT (0),
        CONSTRAINT PK_players PRIMARY KEY CLUSTERED (id),
        CONSTRAINT uk_players_username UNIQUE (username)
    );
END;
GO

-- Leaderboard: ORDER BY high_score DESC
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'idx_players_high_score'
      AND object_id = OBJECT_ID(N'dbo.players')
)
BEGIN
    CREATE NONCLUSTERED INDEX idx_players_high_score
        ON dbo.players (high_score DESC);
END;
GO
