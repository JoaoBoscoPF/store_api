
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Optional
from bson import Decimal128, ObjectId
from pydantic import BaseModel, AfterValidator, Field, ValidationError
from pymongo import MongoClient
from pymongo.collection import Collection
from store.models.base import CreateBaseModel
from store.schemas.base import BaseSchemaMixin, OutSchema

# Configuração do cliente MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['store_database']
collection: Collection = db['products']

class ProductBase(BaseSchemaMixin):
    name: str = Field(..., description="Product name")
    quantity: int = Field(..., description="Product quantity")
    price: Decimal = Field(..., description="Product price")
    status: bool = Field(..., description="Product status")

class ProductIn(ProductBase):
    pass

class ProductOut(ProductIn, OutSchema):
    pass

def convert_decimal_128(v):
    return Decimal128(str(v))

Decimal_ = Annotated[Decimal, AfterValidator(convert_decimal_128)]

class ProductUpdate(BaseSchemaMixin):
    quantity: Optional[int] = Field(None, description="Product quantity")
    price: Optional[Decimal_] = Field(None, description="Product price")
    status: Optional[bool] = Field(None, description="Product status")

class ProductUpdateOut(ProductOut):
    pass

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
            product_data['price'] = Decimal128(product_data['price'])
            result = collection.insert_one(product_data)
            self.id = result.inserted_id
            print(f'Produto salvo com a ID a seguir: {self.id}')
        except ValidationError as e:
            print(f'Erro de validação: {e.json()}')

    def update(self, **kwargs):
        updated_fields = {k: v for k, v in kwargs.items()}
        if 'price' in updated_fields:
            updated_fields['price'] = Decimal128(updated_fields['price'])
        updated_fields['updated_at'] = datetime.now()
        result = collection.update_one({'_id': self.id}, {'$set': updated_fields})
        if result.modified_count:
            for key, value in kwargs.items():
                setattr(self, key, value)
            self.updated_at = updated_fields['updated_at']
            print(f'Produto com ID {self.id} atualizado no nosso sistema!')
        else:
            print(f'Nenhuma atualização feita para o produto com ID {self.id}')

    def delete(self):
        result = collection.delete_one({'_id': self.id})
        if result.deleted_count:
            print(f'Produto com ID {self.id} deletado do nosso sistema')
        else:
            print(f'Produto com ID {self.id} não foi encontrado no nosso sistema')

    @classmethod
    def find_by_id(cls, product_id):
        product_data = collection.find_one({'_id': ObjectId(product_id)})
        if product_data:
            product_data['price'] = Decimal(product_data['price'].to_decimal())
            return cls(**product_data)
        print(f'Produto com ID {product_id} não foi encontrado no nosso sistema')
        print('Tente novamente!')
        return None

    @classmethod
    def list_all(cls):
        products = []
        for product_data in collection.find():
            product_data['price'] = Decimal(product_data['price'].to_decimal())
            products.append(cls(**product_data))
        return products

    def __repr__(self):
        return f"<ProductModel id={self.id}, name={self.name}>"


