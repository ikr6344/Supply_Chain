// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;
pragma experimental ABIEncoderV2;

contract SupplyChain {
    // Propriétaire du contrat
    address public Owner;

    struct Address {
        string text;                // Adresse sous forme de texte
        int256[2] coordinate;      // Tableau de coordonnées [latitude, longitude]
    }

    struct Category {
        uint256 id;
        string title;
        bool isActive;
    }

    constructor() public {
        Owner = msg.sender;
    }

    modifier onlyByOwner() {
        require(msg.sender == Owner, "Only the owner can perform this action");
        _;
    }

    enum STAGE {
        Manufacture,
        Distribution,
        Retail,
        Sold
    }

    uint256 public rmsCtr = 0;
    uint256 public productCtr = 0;
    uint256 public userCount = 0;
    uint256 public categoryCtr = 0;

    struct Product {
        uint256 id;
        string name;
        string description;
        uint256[] rwIds;
        uint256 price; // Ajout du prix
        Category category;
        uint256 manufacturerId;
        uint256 distributorId;
        uint256 retailerId;
        bool isActive;
        string image;
        uint256 currentHandlerId;
        STAGE stage;
    }

    struct RW {
        uint256 id;
        string name;
        string description;
        uint256 price;
        uint256 userId;
        string image;
        Address origin; // Utilisation de la structure Address
    }

    struct User {
        uint256 id;
        string name;
        string email;
        bytes32 passwordHash; // Stockage sécurisé avec un hash
        string role; // Role de l'utilisateur comme une chaîne de caractères
    }

    struct ProductHistory {
        uint256 timestamp;
        uint256 handlerId;
        STAGE stage;
    }

    mapping(uint256 => User) public users;
    mapping(uint256 => RW) public rms;
    mapping(uint256 => Product) public productStock;
    mapping(uint256 => Category) public categories;
    mapping(uint256 => ProductHistory[]) public productHistories;

    // Événements
    event RawMaterialAdded(uint256 id, string name);
    event ProductAdded(uint256 id, string name);
    event ProductStageUpdated(uint256 id, STAGE newStage);
    event CategoryAdded(uint256 id, string title);
    event RawMaterialUpdated(uint256 id, string name);
    event ProductUpdated(uint256 id, string name);
    event CategoryUpdated(uint256 id, string title);

    // Ajouter une matière première
    function addRawMaterial(
        string memory _name,
        string memory _description,
        uint256 _price,
        string memory _image,
        string memory _originText, // Texte de l'adresse
        int256 _latitude,          // Latitude
        int256 _longitude          // Longitude
    ) public onlyByOwner {
        rmsCtr++;
        rms[rmsCtr] = RW({
            id: rmsCtr,
            name: _name,
            description: _description,
            price: _price,
            userId: 0,
            image: _image,
            origin: Address({
                text: _originText,
                coordinate: [_latitude, _longitude] // Remplissage des coordonnées
            })
        });
        emit RawMaterialAdded(rmsCtr, _name);
    }

    // Ajouter une catégorie
    function addCategory(string memory _title) public onlyByOwner {
        categoryCtr++;
        categories[categoryCtr] = Category({
            id: categoryCtr,
            title: _title,
            isActive: true
        });
        emit CategoryAdded(categoryCtr, _title);
    }

    // Ajouter un utilisateur
    function addUser(
        string memory _name,
        string memory _email,
        string memory _password,
        string memory _role
    ) public {
        require(bytes(_name).length > 0, "Name cannot be empty");
        require(bytes(_email).length > 0, "Email cannot be empty");
        require(bytes(_password).length > 0, "Password cannot be empty");
        userCount++;
        users[userCount] = User({
            id: userCount,
            name: _name,
            email: _email,
            passwordHash: keccak256(abi.encodePacked(_password)),
            role: _role
        });
    }

    // Ajouter un produit
    function addProduct(
        string memory _name,
        string memory _description,
        uint256[] memory _rwIds,
        uint256 _manufacturerId,
        uint256 _categoryId,
        uint256 _price,  // Ajouter le prix comme paramètre
        string memory _image
    ) public onlyByOwner {
        // Vérification des IDs de matières premières
        for (uint256 i = 0; i < _rwIds.length; i++) {
            require(_rwIds[i] > 0 && _rwIds[i] <= rmsCtr, "Invalid raw material ID");
        }

        // Vérification de la validité de la catégorie
        require(_categoryId > 0 && _categoryId <= categoryCtr, "Invalid category ID");

        // Incrémentation du compteur de produits
        productCtr++;

        // Création du produit
        productStock[productCtr] = Product({
            id: productCtr,
            name: _name,
            description: _description,
            rwIds: _rwIds,
            price: _price,  // Assignation du prix
            category: categories[_categoryId],
            manufacturerId: _manufacturerId,
            distributorId: 0,
            retailerId: 0,
            currentHandlerId: _manufacturerId,
            stage: STAGE.Manufacture,  // Le stade initial est la fabrication
            isActive: true,
            image: _image
        });

        // Émettre l'événement
        emit ProductAdded(productCtr, _name);
    }

    // Obtenir un produit par ID
    function getProductById(uint256 _productId) public view returns (Product memory) {
        require(_productId > 0 && _productId <= productCtr, "Produit inexistant");
        return productStock[_productId];
    }

    // Obtenir tous les produits
    function getAllProducts() public view returns (Product[] memory) {
        uint256 count = productCtr; // Nombre total de produits
        Product[] memory allProducts = new Product[](count);

        for (uint256 i = 1; i <= count; i++) {
            allProducts[i - 1] = productStock[i];
        }

        return allProducts;
    }

    // Obtenir toutes les catégories
function getAllCategories() public view returns (Category[] memory) {
    uint256 count = categoryCtr; // Nombre total de catégories
    // Créer un tableau dynamique avec le nombre total de catégories
    Category[] memory allCategories = new Category[](count);

    // Remplir le tableau allCategories avec les catégories
    for (uint256 i = 1; i <= count; i++) {
        allCategories[i - 1] = categories[i]; // Assurez-vous que 'categories' commence à 1
    }

    return allCategories;
}


    // Obtenir les utilisateurs par rôle
    function getUsersByRole(string memory _role) public view returns (User[] memory) {
        uint256 count = userCount; // Nombre total d'utilisateurs
        uint256 userCountByRole = 0;

        // Compter le nombre d'utilisateurs avec le rôle spécifié
        for (uint256 i = 1; i <= count; i++) {
            if (keccak256(abi.encodePacked(users[i].role)) == keccak256(abi.encodePacked(_role))) {
                userCountByRole++;
            }
        }

        // Créer un tableau dynamique avec le nombre d'utilisateurs avec ce rôle
        User[] memory usersWithRole = new User[](userCountByRole);
        uint256 index = 0;

        // Ajouter les utilisateurs avec le rôle spécifié
        for (uint256 i = 1; i <= count; i++) {
            if (keccak256(abi.encodePacked(users[i].role)) == keccak256(abi.encodePacked(_role))) {
                usersWithRole[index] = users[i];
                index++;
            }
        }

        return usersWithRole;
    }

    // Mettre à jour le stade d'un produit
    function updateProductStage(uint256 _productId, STAGE _newStage) public onlyByOwner {
        require(_productId > 0 && _productId <= productCtr, "Produit inexistant");
        require(
            uint8(_newStage) > uint8(productStock[_productId].stage),
            "Stade invalide"
        );
        productStock[_productId].stage = _newStage;

        productHistories[_productId].push(
            ProductHistory({
                timestamp: block.timestamp,
                handlerId: productStock[_productId].currentHandlerId,
                stage: _newStage
            })
        );

        emit ProductStageUpdated(_productId, _newStage);
    }

 function getAllRawMaterials() public view returns (RW[] memory) {
        uint256 count = rmsCtr; // Nombre total de matières premières
        // Créer un tableau dynamique avec le nombre total de matières premières
        RW[] memory allRawMaterials = new RW[](count);
        for (uint256 i = 1; i <= count; i++) {
            allRawMaterials[i - 1] = rms[i];
        }
         return allRawMaterials;
    }
}
