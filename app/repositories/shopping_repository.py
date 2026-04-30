from app.models.lista_compras import ListaCompras
from app.models.historico_compras import HistoricoCompras
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

class ShoppingRepository:
    
    @staticmethod
    def check_if_product_has_been_added_in_last_48_hours(db: Session, item: str):
        item = db.query(ListaCompras).filter(ListaCompras.nome_item == item).filter(ListaCompras.data_criacao >= datetime.now() - timedelta(hours=48)).first()
        return item

    @staticmethod
    def add_item_to_list(db: Session, user: str, item: str, quantidade: int = 1):
        item_db = ListaCompras(
            user=user,
            nome_item=item,
            quantidade=quantidade,
            data_criacao=datetime.now()
        )
        db.add(item_db)
        db.commit()
        db.refresh(item_db)
        return item_db

    @staticmethod
    def remove_item_from_list(db: Session, item: str):
        item_db = db.query(ListaCompras).filter(ListaCompras.nome_item == item).first()
        if item_db:
            db.delete(item_db)
            db.commit()
            return item_db
        else:
            return False

    @staticmethod
    def get_all_items_from_list(db: Session):
        return db.query(ListaCompras).all()

    @staticmethod
    def add_shopping_to_history(db: Session, user: str, valor: float = 0.0):
        shopping = HistoricoCompras(
            user=user,
            gasto_valor=valor,
            data_compra=datetime.now()
        )
        db.add(shopping)
        db.commit()
        db.refresh(shopping)
        
        