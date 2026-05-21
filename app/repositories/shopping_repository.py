from app.models.lista_compras import ListaCompras
from app.models.historico_compras import HistoricoCompras
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.users import Users

class ShoppingRepository:
    
    @staticmethod
    def check_if_product_has_been_added_in_last_48_hours(db: Session, item: str):
        item = db.query(ListaCompras).filter(ListaCompras.nome_item == item).filter(ListaCompras.data_criacao >= datetime.now() - timedelta(hours=48)).first()
        return item

    @staticmethod
    def add_item_to_list(db: Session, user: str, item: str, quantidade: int = 1):
        from app.models.users import Users
        db_user = db.query(Users).filter(Users.user_name == user).first()
        if not db_user:
            raise ValueError(f"Usuário '{user}' não encontrado no banco de dados.")
            
        item_db = ListaCompras(
            usuario=db_user,
            user_name=db_user.user_name,
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
    def remove_all_items_from_list(db: Session):
        db.query(ListaCompras).delete()
        db.commit()

    @staticmethod
    def add_shopping_to_history(db: Session, user: str, valor: float = 0.0, supermercado: str = None, itens: list = None):
        db_user = db.query(Users).filter(Users.user_name == user).first()
        if not db_user:
            raise ValueError(f"Usuário '{user}' não encontrado no banco de dados.")
            
        shopping = HistoricoCompras(
            usuario=db_user,
            user_name=db_user.user_name,
            gasto_valor=valor,
            data_compra=datetime.now(),
            supermercado=supermercado,
            lista_itens_comprados=itens
        )
        db.add(shopping)
        db.commit()
        db.refresh(shopping)

    @staticmethod
    def get_all_items_from_history(db: Session, user: str, periodo: str = "mês atual"):
        if periodo == "30 dias":
            return db.query(HistoricoCompras)\
            .filter(HistoricoCompras.data_compra >= datetime.now() - timedelta(days=30))\
            .filter(HistoricoCompras.user_name == user)\
            .order_by(HistoricoCompras.data_compra.asc())\
            .all()
        else:
            return db.query(HistoricoCompras)\
            .filter(HistoricoCompras.data_compra >= datetime.now().replace(day=1))\
            .filter(HistoricoCompras.user_name == user)\
            .order_by(HistoricoCompras.data_compra.asc())\
            .all()