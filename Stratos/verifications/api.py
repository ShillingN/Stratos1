from db import Session
from .entities import Verification
import notify


def get_verifications():
    with Session() as db_session:
        verifications = db_session.query(Verification).all()
    return verifications


def check_verification(card_number, user_email):
    with Session() as db_session:
        verification = db_session.query(Verification).filter(Verification.card_number == card_number,
                                                         Verification.user_email == user_email,
                                                         Verification.status == 1).first()
        if verification is None:
            return False
    return True


def get_verification_by_id(verify_id):
    with Session() as db_session:
        verification = db_session.query(Verification).filter(Verification.id == verify_id).first()
    return verification


def create_verification(card_number, user_id, user_email, photo):
    with Session() as db_session:
        verification = db_session.query(Verification).filter(Verification.card_number == card_number,
                                                             Verification.user_email == user_email,
                                                             Verification.status == 0).first()
        if verification is not None:
            db_session.close()
            return verification

        verification = Verification(card_number=card_number, user_id=user_id, user_email=user_email, photo=photo)
        db_session.add(verification)
        db_session.commit()

        notify.send_message('Новая заявка на верификацию\n\n{}\n{}'.format(user_email, card_number))
        return verification.id
