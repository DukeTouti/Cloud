CREATE TABLE seances (
	id          INT IDENTITY PRIMARY KEY,
	semaine     INT           NOT NULL,
	annee       INT           NOT NULL,
	jour        NVARCHAR(10)  NOT NULL,
	heure_debut TIME          NOT NULL,
	heure_fin   TIME          NOT NULL,
	matiere     NVARCHAR(100) NOT NULL,
	type_seance NVARCHAR(5)   NOT NULL,
	salle       NVARCHAR(20),
	prof        NVARCHAR(100),
	filiere     NVARCHAR(50)  NOT NULL,
	groupe      NVARCHAR(5)   NOT NULL
);

CREATE INDEX ix_seances_lookup
	ON seances (filiere, semaine, annee, type_seance, groupe);
