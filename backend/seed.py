from app import create_app
from app.extensions import db
from app.models.savoir_agir import SavoirAgir
from app.models.jalon import Jalon

app = create_app()

with app.app_context():
    db.create_all()

    names = [
        "specifier",
        "modeliser",
        "communiquer",
        "concevoir",
        "developper",
        "gerer"
    ]

    for name in names:
        sa = SavoirAgir(name=name)
        db.session.add(sa)
        db.session.flush()

        for i in range(1, 4):
            db.session.add(Jalon(name=f"jalon{i}", savoir_agir_id=sa.id))

    db.session.commit()

print("Seed complete 🚀")