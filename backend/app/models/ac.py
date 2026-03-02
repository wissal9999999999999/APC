from datetime import datetime
from app.extensions import db

class ApprentissageCritique(db.Model):
    __tablename__ = "apprentissage_critique"

    id = db.Column(db.Integer, primary_key=True)

    savoir_agir_id = db.Column(
        db.Integer,
        db.ForeignKey("savoir_agir.id"),
        nullable=False
    )

    jalon_id = db.Column(
        db.Integer,
        db.ForeignKey("jalon.id"),
        nullable=False
    )

    ac_text = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)