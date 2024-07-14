
from datetime import datetime
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import ObjectId
from pydantic import BaseModel, Field, ValidationError
from store.models.base import CreateBaseModel
from store.schemas.product import ProductIn

# Configuração do cliente MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['store_database']
collection: Collection = db['products']

class ProductModel(ProductIn, CreateBaseModel):
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __init__(self, **data):
        super().__init__(**data)
        if not hasattr(self, 'created_at'):
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def save(self):
        try:
            product_data = self.dict(by_alias=True)
            result = collection.insert_one(product_data)
            self.id = result.inserted_id
            print(f'Produto salvo com ID a seguir: {self.id}')
        except ValidationError as e:
            print(f'Erro de validação: {e.json()}')

    def update(self, **kwargs):
        updated_fields = {k: v for k, v in kwargs.items()}
        updated_fields['updated_at'] = datetime.now()  # Atualiza o campo updated_at para o tempo atual
        
        try:
            result = collection.update_one({'_id': self.id}, {'$set': updated_fields})
            if result.matched_count == 0:
                raise ProductNotFoundError(f'Produto com ID {self.id} não encontrado.')
            
            if result.modified_count:
                # Atualiza os atributos do objeto com os novos valores
                for key, value in kwargs.items():
                    setattr(self, key, value)
                self.updated_at = updated_fields['updated_at']  # Atualiza o atributo updated_at do objeto
                print(f'Produto com ID {self.id} atualizado no nosso sistema!')
            else:
                print(f'Nenhuma atualização feita para o produto com ID {self.id}')
        
        except PyMongoError as e:
            raise DatabaseError(f'Erro ao acessar o banco de dados: {str(e)}')

    class ProductNotFoundError(Exception):
        def __init__(self, message="Produto não encontrado."):
            self.message = message
            super().__init__(self.message)

    def delete(self):
        result = collection.delete_one({'_id': self.id})
        if result.deleted_count:
            print(f'Produto com ID {self.id} deletado')
        else:
            print(f'Produto com ID {self.id} não encontrado')

    @classmethod
    def find_by_id(cls, product_id):
        product_data = collection.find_one({'_id': ObjectId(product_id)})
        if product_data:
            return cls(**product_data)
        print(f'Produto com ID {product_id} não foi encontrado no nosso sistema')
        return None

    @classmethod
    def list_all(cls):
    products = []
    filter_query = {
        'price': {
            '$gt': Decimal128('5000'),
            '$lt': Decimal128('8000')
        }
    }
    for product_data in collection.find(filter_query):
        product_data['price'] = Decimal(product_data['price'].to_decimal())
        products.append(cls(**product_data))
    return products


    def __repr__(self):
        return f"<ProductModel id={self.id}, name={self.name}>"

