import json
from pathlib import Path
from pydantic import BaseModel
from web3 import Web3
from typing import Any
from fastapi import FastAPI, HTTPException, Depends
import jwt
from datetime import datetime, timedelta
from typing import List 
# OAuth2 Scheme for token verification
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from model import *
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import Field
# Load contract details
supply_chain_path = Path("./artifacts/SupplyChain.json")
with supply_chain_path.open("r") as file:
    supply_chain_data = json.load(file)

app = FastAPI()
origins = [
    "http://localhost",  # Allow localhost
    "http://localhost:5173",  # React dev server (if applicable)
    
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow these origins to access the API
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Blockchain setup
CHAIN_ID = 1337
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

if not w3.is_connected():
    raise Exception("Unable to connect to Ganache")

# Contract details
network_id = 5777
network_data = supply_chain_data["networks"].get(str(network_id))
if not network_data:
    raise Exception(f"Contract address not found for network ID {network_id}.")

contract_abi = supply_chain_data.get("abi")
CONTRACT_ADDRESS = network_data["address"]
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

# Owner account details
owner_address = "0x5c8b23638aCA975e6841C0e7DeD38F8D1f31310A"
private_key = "0x960a980bbcfb05f132f8bbf21ec76647cf5c47a217ac9b1080f6aecd4c0d56b8"
# JWT Secret Key for token generation
SECRET_KEY = "AZERTGUYIMJLKJ?V123456789LK?NB0JHGFFDJ"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
### Models ###
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str
    userAddress: str

class RawMaterialCreate(BaseModel):
    name: str
    description: str
    price: int
    image: str
    origin: str  # Adresse sous forme de texte
    latitude: float
    longitude: float
    userId:int

class AddCategoryRequest(BaseModel):
    title: str



class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


class CreateShipmentRequest(BaseModel):
    sender_id: int
    receiver_id: int
    distributor_id: int
    pickup_time: int  # Adjusted to handle ISO 8601 datetime strings
    distance: int        # Adjusted to allow fractional values
    price: int
    description: str

class User2(BaseModel):
    id: int
    email: str
    name:str
    

class Shipment(BaseModel):
    id:int
    senderId: int
    senderName: str
    receiverId: int
    receiverName: str
    distributorId: int
    pickupTime: datetime | None = Field(None, description="Pickup time as a datetime")
    deliveryTime: datetime | None = Field(None, description="Delivery time as a datetime")
    distance: int
    price: int
    description: str
    status: int  # Use an Enum or int for status (0: Pending, 1: InTransit, 2: Delivered, 3: Canceled)
    isPaid: bool
class Config:
        # Allow parsing UNIX timestamps into datetime objects automatically
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,  # Handle None gracefully
        }

### Helper Functions ###

# Route pour obtenir les utilisateurs par rôle
@app.get("/users/{role}", response_model=list[User2])
async def get_users_by_role(role: str):
    try:
        # Appeler la fonction du contrat pour récupérer les utilisateurs par rôle
        users_data = contract.functions.getUsersByRole(role).call()

        # Si des utilisateurs existent, les retourner
        users_list = [User2(id=user[0],name=user[1], email=user[2]) for user in users_data]
        return users_list
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Function to generate JWT token
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Function to hash the password and verify against the contract's password hash
def verify_password(plain_password: str, stored_password_hash: bytes):
    # Generate the hash from the plain password
    hashed_password = Web3.keccak(plain_password.encode('utf-8'))
    
    # Debugging
    print(f"Debug: Hashed Password = {hashed_password}, Stored Hash = {stored_password_hash}")
    
    # Compare the raw binary hash with the stored hash
    return hashed_password == stored_password_hash

# Function to get user from the blockchain (in real use, retrieve from a DB or blockchain)
def get_user_from_blockchain(email: str):
    # Example function that retrieves user details from blockchain
    users_count = contract.functions.userCount().call()
    for i in range(1, users_count + 1):
        user = contract.functions.users(i).call()  # Assuming this returns (name, email, password, role, address)
        if user[2] == email:
            return user
    return None

### API Endpoints ###
@app.post("/login/", response_model=Token)
async def login(user: UserLogin):
    # Fetch the user from blockchain (simulating a DB lookup)
    db_user = get_user_from_blockchain(user.email)
    
    if not db_user:
        raise HTTPException(status_code=401, detail="user not found")
    
    # Verify the password (In real implementation, it would be hashed)
    if not verify_password(user.password, db_user[3]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.email, "role": db_user[4],"iduser":db_user[0]}) 
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/add_user/")
async def add_user(user: UserCreate):
    try:
        nonce = w3.eth.get_transaction_count(owner_address)
        
        tx = contract.functions.addUser(
            user.name,
            user.email,
            user.password,
            user.role,
            user.userAddress
        ).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            return {"status": "success", "tx_hash": tx_hash.hex()}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Protected route that requires JWT authentication
@app.get("/protected/")
async def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Here, you can fetch the user from blockchain or DB based on the email
        user = get_user_from_blockchain(email)
        if user:
            return {"msg": f"Hello {user[0]}, you have access to this protected route!"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/raw_materials/")
async def add_raw_material(raw_material: RawMaterialCreate):
    try:
        # Construction de la transaction
        nonce = w3.eth.get_transaction_count(owner_address)
        tx = contract.functions.addRawMaterial(
            raw_material.name,
            raw_material.description,
            raw_material.price,
            raw_material.image,
            raw_material.origin,
            int(raw_material.latitude * 10**6),  # Conversion en int pour Solidity
            int(raw_material.longitude * 10**6),  # Conversion en int pour Solidity
            raw_material.userId,

        ).build_transaction({
            'chainId': 1337,  # ID de votre réseau (1337 = Ganache local)
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    # Attendre que la transaction soit minée
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # Vérification du statut de la transaction
        if receipt.status == 1:
            return {"status": "success", "tx_hash": tx_hash.hex()}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create_shipment")
async def create_shipment(payload: CreateShipmentRequest):
    try:
        # Extract data from the payload
        data = payload.dict()
        sender_id = data['sender_id']
        receiver_id = data['receiver_id']
        distributor_id = data['distributor_id']
        pickup_time = data['pickup_time']
        distance = data['distance']
        price = data['price']
        description=data['description']

        # Remaining code for transaction logic
        nonce = w3.eth.get_transaction_count(owner_address)
        tx = contract.functions.createShipment(
            sender_id,
            receiver_id,
            distributor_id,
            pickup_time,
            distance,
            price,
            description
        ).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 1:
            return {"status": "success", "tx_hash": tx_hash.hex()}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/start_shipment/{shipment_index}")
async def start_shipment(shipment_index: int):
    try:
        nonce = w3.eth.get_transaction_count(owner_address)
        tx = contract.functions.startShipment(shipment_index).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            return {"status": "success", "tx_hash": tx_hash.hex()}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/complete_shipment/{shipment_index}")
async def complete_shipment(shipment_index: int):
    try:
        nonce = w3.eth.get_transaction_count(owner_address)
        tx = contract.functions.completeShipment(shipment_index).build_transaction({
            'chainId': CHAIN_ID,
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status == 1:
            return {"status": "success", "tx_hash": tx_hash.hex()}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# New endpoint: Get users by role
from fastapi import HTTPException
from typing import Optional

@app.get("/getUser/{user_id}")
async def get_user_by_id(user_id: int):

    try:
        
        users_count = contract.functions.userCount().call()

        for i in range(1, users_count + 1):
            user = contract.functions.users(i).call()  # Assuming this returns (id, name, email, cne, role, address)
            
            # Log the raw user data to debug
            print(f"Raw user data: {user}")

            if user[0] == user_id:
                return {
                    "id": user[0],
                    "name": user[1],
                    "email": user[2],
                    "cne": user[3],
                    "role": user[4],
                    "address": user[5]
                }

        return {"error": "User not found"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

# New endpoint: Get product history
@app.get("/get_product_history/{product_id}")
async def get_product_history(product_id: int):
    try:
        product_history = contract.functions.getProductHistory(product_id).call()
        history = []

        for entry in product_history:
            history.append({
                "timestamp": entry[0],
                "status": entry[1],  # Assuming status is the 2nd element
                "location": entry[2],  # Assuming location is the 3rd element
            })

        return {"product_id": product_id, "history": history}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Function to fetch user data directly from the smart contract
def get_user_data(user_id: int) -> dict:
    try:
        user_data = contract.functions.users(user_id).call()
        return {"name": user_data[1]}  # Assuming the user's name is at index 0
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching user data for ID {user_id}: {str(e)}")

@app.get("/shipments", response_model=List[Shipment])
async def get_shipments():
    try:
        ship_count = contract.functions.shipmentCount().call()
        result = []
        for i in range(1, ship_count + 1):
            shipment = contract.functions.shipments(i).call()
            sender_data = get_user_data(shipment[1])  
            receiver_data = get_user_data(shipment[2])  
            pickup_time = datetime.fromtimestamp(shipment[4]) if shipment[4] else None
            delivery_time = datetime.fromtimestamp(shipment[5]) if shipment[5] else None

            # Create Shipment object with sender and receiver names
            shipment_data = Shipment(
                id=shipment[0],
                senderId=shipment[1],
                senderName=sender_data["name"],
                receiverId=shipment[2],
                receiverName=receiver_data["name"],
                distributorId=shipment[3],
                pickupTime=pickup_time,
                deliveryTime=delivery_time,
                distance=shipment[6],
                price=shipment[7],
                description=shipment[8],
                status=shipment[9],
                isPaid=shipment[10]
            )
            result.append(shipment_data)

        # Return the shipment data
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching shipments: {str(e)}")


# Endpoint to get shipments by distributor ID
@app.get("/shipments/{distributor_id}", response_model=List[Shipment])
async def get_shipments_by_distributor(distributor_id: int):
    try:
        # Call the smart contract method to get shipments by distributor ID
        shipments = contract.functions.getShipmentsByDistributor(distributor_id).call()

        # For each shipment, fetch the sender and receiver names using the user contract
        result = []
        for shipment in shipments:
            sender_data = get_user_data(shipment[1])  
            receiver_data = get_user_data(shipment[2])  
            pickup_time = datetime.fromtimestamp(shipment[4]) if shipment[4] else None
            delivery_time = datetime.fromtimestamp(shipment[5]) if shipment[5] else None

            # Create Shipment object with sender and receiver names
            shipment_data = Shipment(
                id=shipment[0],
                senderId=shipment[1],
                senderName=sender_data["name"],
                receiverId=shipment[2],
                receiverName=receiver_data["name"],
                distributorId=shipment[3],
                pickupTime=pickup_time,
                deliveryTime=delivery_time,
                distance=shipment[6],
                price=shipment[7],
                description=shipment[8],
                status=shipment[9],
                isPaid=shipment[10]
            )
            result.append(shipment_data)

        # Return the shipment data
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching shipments: {str(e)}")
@app.get("/raw_materials/")
async def get_all_raw_materials():
    try:
        # Appel à la fonction `getAllRawMaterials` du contrat
        raw_materials_data = contract.functions.getAllRawMaterials().call()

        # Transformation des données en un format lisible
        raw_materials_list = [
            {
                "id": raw_material[0],  # ID
                "name": raw_material[1],  # Nom
                "description": raw_material[2],  # Description
                "price": raw_material[3],  # Prix
                "userId": raw_material[4],  # ID de l'utilisateur
                "image": raw_material[5],  # Image
                "origin": {
                    "text": raw_material[6][0],  # Texte de l'adresse
                    "coordinate": [
                raw_material[6][1][0] / 10**6,  # Convertir la latitude de micro-degrés en degrés
                raw_material[6][1][1] / 10**6,  # Convertir la longitude de micro-degrés en degrés
            ], 
                },
            }
            for raw_material in raw_materials_data
        ]

        return raw_materials_list
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
# Ajouter une catégorie
@app.post("/add_category/")
def add_category(request: AddCategoryRequest):
    try:
        tx = contract.functions.addCategory(request.title).transact({'from': w3.eth.accounts[0]})
        w3.eth.wait_for_transaction_receipt(tx)
        return {"message": "Category added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products/")
async def add_product(product: AddProductRequest):
    try:
        # Vérification de la validité des IDs de matières premières (par rapport à votre logique Solidity)
        for rw_id in product.rwIds:
            if rw_id <= 0 or rw_id > 1000:  # Ajustez cette logique en fonction de votre contrat
                raise HTTPException(status_code=400, detail=f"Invalid raw material ID: {rw_id}")

        # Vérification de la validité de la catégorie
        if product.categoryId <= 0 or product.categoryId > 1000:  # Ajustez cette logique
            raise HTTPException(status_code=400, detail="Invalid category ID")

        # Construction de la transaction
        nonce = w3.eth.get_transaction_count(owner_address)
        tx = contract.functions.addProduct(
            product.name,
            product.description,
            product.rwIds,
            int(product.price),
            product.manufacturerId,
            product.distributorId,
            product.categoryId,
            product.productAddress,
            product.image
        ).build_transaction({
            'chainId': 1337,  # ID de votre réseau (1337 = Ganache local, ajustez selon votre réseau)
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': nonce,
        })

        # Signature et envoi de la transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Attente du reçu de la transaction
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # Vérification du statut de la transaction
        if receipt.status == 1:
            return {"status": "success", "tx_hash": tx_hash.hex()}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Récupérer une catégorie par ID
@app.get("/get_category/{category_id}")
def get_category(category_id: int):
    try:
        category = contract.functions.getCategoryById(category_id).call()
        if category[0] == 0:
            raise HTTPException(status_code=404, detail="Category not found")
        return {
            "id": category[0],
            "title": category[1],
            "isActive": category[2]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/products/{category_id}")
def get_category(category_id: int):
    try:
        category = contract.functions.getProductById(category_id).call()
        if category[0] == 0:
            raise HTTPException(status_code=404, detail="Category not found")
        return {
            "id": category[0],
            "name": category[1],
            "rwIds": category[3],
            "ManufacteurId":category[6],
            "produitOriginID":category[11],
            "productAddress":category[8]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Récupérer une matière première par ID
@app.get("/get_raw_material/{raw_material_id}")
def get_raw_material(raw_material_id: int):
    try:
        raw_material = contract.functions.getRawMaterialById(raw_material_id).call()
        if raw_material[0] == 0:
            raise HTTPException(status_code=404, detail="Raw material not found")
        return {
            "id": raw_material[0],
            "name": raw_material[1],
            "description": raw_material[2],
            "price": raw_material[3],
            "userId": raw_material[4],
            "image": raw_material[5],
            "origin": {
                "text": raw_material[6],
                "coordinate": raw_material[7]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Modifier un produit
@app.put("/edit_product/{product_id}")
def edit_product(product_id: int, request: EditProductRequest):
    try:
        tx = contract.functions.editProduct(
            product_id,
            request.name,
            request.description,
            request.rwIds,
            request.categoryId,
            request.image
        ).transact({'from': w3.eth.accounts[0]})
        w3.eth.wait_for_transaction_receipt(tx)
        return {"message": "Product updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Modifier une catégorie
@app.put("/edit_category/{category_id}")
def edit_category(category_id: int, request: EditCategoryRequest):
    try:
        tx = contract.functions.editCategory(category_id, request.title).transact({'from': w3.eth.accounts[0]})
        w3.eth.wait_for_transaction_receipt(tx)
        return {"message": "Category updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/products/", response_model=List[Any])
async def get_all_products():
    try:
        # Appel de la fonction `getAllProducts` du contrat
        products_data = contract.functions.getAllProducts().call()

        # Transformation des données en un format lisible
        products_list = [
            {
                "id": product[0],  # ID du produit
                "name": product[1],  # Nom
                "description": product[2],  # Description
                "rwIds": product[3],  # Liste des IDs des matières premières utilisées
                "price": product[4],  # ID du fabricant
                "categoryId": {
                    "id": product[5][0],  # ID de la catégorie
                    "title": product[5][1],  # Nom de la catégorie
                    "isActive": product[5][2],  # Statut d'activation de la catégorie
                },

                "image": product[10],  
                "isActive": product[9],
                "ManufacteurId": product[6],
                "productAddress":product[8],
                "produitOriginID":product[11], 
                "stage":product[12]
            }
            for product in products_data
        ]

        return products_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/manufacturer/{manufacturer_id}")
async def get_products_by_manufacturer_id(manufacturer_id: int):
    try:
        # Appel de la fonction `getProductsByManufacturerId` du contrat
        products_data = contract.functions.getProductsByManufacturerId(manufacturer_id).call()

        # Transformation des données en un format lisible
        products_list = [
            {
                "id": product[0],  # ID du produit
                "name": product[1],  # Nom
                "description": product[2],  # Description
                "rawMaterialIds": product[3],  # Liste des IDs des matières premières utilisées
                "manufacturerId": product[4],  # ID du fabricant
                "categoryId": product[5],  # ID de la catégorie
                "image": product[6],  # URL de l'image
                "isActive": product[7],  # Statut d'activité
            }
            for product in products_data
        ]

        return {"products": products_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories/")
def get_all_categories():
    try:
        # Appel de la fonction Solidity `getAllCategories`
        categories = contract.functions.getAllCategories().call()

        # Transformation des données en un format lisible
        result = [
            {
                "id": category[0],
                "title": category[1],
                "isActive": category[2]
            }
            for category in categories
        ]

        return  result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

class UpdateStageProductRequest(BaseModel):
    product_id: int
    stage: int  # Par exemple : "manufacturing", "shipping", "delivered"

@app.put("/update_stage_product/{product_id}")
async def update_stage_product(product_id: int, request: UpdateStageProductRequest):
    try:
        # Appel à la fonction de mise à jour de l'état du produit sur le contrat
        nonce = w3.eth.get_transaction_count(owner_address)
        tx = contract.functions.updateProductStage(
            product_id,
            request.stage
        ).build_transaction({
            'chainId': 1337,  # ID de la chaîne Ganache
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': nonce,
        })

        # Signature de la transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Attente de la confirmation de la transaction
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            return {"status": "success", "tx_hash": tx_hash.hex()}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Route pour obtenir l'historique complet d'un produit par son ID
@app.get("/get_product_history/{product_id}")
async def get_product_history(product_id: int):
    try:
        # Vérification de la validité du produit
        if product_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid product ID")

        # Appel à la fonction Solidity pour récupérer l'historique du produit
        history = contract.functions.getProductHistory(product_id).call()

        # Retourner l'historique sous forme d'une réponse JSON
        return {"history": history}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@app.post("/duplicate_product")
async def duplicate_product(request: DuplicateProductRequest):
    try:
        if any(rw_id <= 0 for rw_id in request.rwIds):
            raise HTTPException(status_code=400, detail="Invalid raw material ID(s)")

        # Extraire les paramètres de la requête
        produitOriginID = request.produitOriginID
        newName = request.newName
        newDescription=request.newDescription
        newPrice =int( request.newPrice  ) 
        rwIds =request.rwIds
        newImage = request.newImage
        distributorId=request.distributorId
        newAddress=request.newAddress
        manufacturerIdNew=request.manufacturerIdNew

        # Appel à la fonction Solidity "duplicateProduct"
        nonce = w3.eth.get_transaction_count(owner_address)
        tx = contract.functions.duplicateProduct(
            produitOriginID,
            newName,
            newDescription,
            rwIds,
            newPrice,
            manufacturerIdNew,
            distributorId,
            newAddress,
            newImage,
            
            
        ).build_transaction({
            'chainId': 1337,  # ID du réseau, ici pour Ganache
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': nonce,
        })

        # Signer la transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Attendre que la transaction soit minée
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # Vérification du statut de la transaction
        if receipt.status == 1:
            return {"status": "success", "tx_hash": tx_hash.hex()}
        else:
            raise HTTPException(status_code=400, detail="Transaction failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
