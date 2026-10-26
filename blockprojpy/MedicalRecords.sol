// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MedicalRecords {

    address public admin;

    struct Doctor {
        string doctorId;
        string username;
        bytes32 passwordHash;
        string specialty;
        bool isAuthorized;
    }

    struct Patient {
        string name;
        uint256 age;
        string addressPatient;
        string hmo;
    }

    struct Medication {
        string name;
        uint256 dosage;
        uint256 stock;
    }

    struct Record {
        string patientId;
        string doctorId;
        string treatmentDetails;
        uint256 timestamp;
    }

    mapping(address => Doctor) public doctors;
    mapping(string => Patient) public patients;
    mapping(string => Record[]) public records;
    mapping(uint256 => Medication) public medications; // תרופות לפי מזהה
    address[] public doctorAddresses;
    string[] public patientIds;
    uint256 public medicationCounter; // מזהה תרופה ייחודי

    constructor() {
        admin = msg.sender;
        medicationCounter = 0; // אתחול של מונה התרופות
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action.");
        _;
    }

    modifier onlyAuthorizedDoctor() {
        require(doctors[msg.sender].isAuthorized, "Only authorized doctors can perform this action.");
        _;
    }

    function addDoctor(
        address doctorAddress,
        string memory _doctorId,
        string memory _username,
        string memory _password,
        string memory _specialty
    ) public onlyAdmin {
        bytes32 passwordHash = keccak256(abi.encodePacked(_password));
        doctors[doctorAddress] = Doctor(_doctorId, _username, passwordHash, _specialty, true);
        doctorAddresses.push(doctorAddress);
    }

    function removeDoctor(address doctorAddress) public onlyAdmin {
        doctors[doctorAddress].isAuthorized = false;
    }

    function addPatient(
        string memory _patientId,
        string memory _name,
        uint256 _age,
        string memory _addressPatient,
        string memory _hmo
    ) public onlyAuthorizedDoctor {
        patients[_patientId] = Patient(_name, _age, _addressPatient, _hmo);
        patientIds.push(_patientId);
    }

    function getDoctors() public view returns (address[] memory) {
        return doctorAddresses;
    }

    function getPatientIds() public view returns (string[] memory) {
        return patientIds;
    }

    function getPatient(string memory _patientId) public view returns (string memory, uint256, string memory, string memory) {
        Patient memory patient = patients[_patientId];
        return (patient.name, patient.age, patient.addressPatient, patient.hmo);
    }

    function addRecord(
        string memory _patientId,
        string memory _doctorId,
        string memory _treatmentDetails
    ) public onlyAuthorizedDoctor {
        require(bytes(patients[_patientId].name).length != 0, "Patient does not exist.");
        records[_patientId].push(Record(_patientId, _doctorId, _treatmentDetails, block.timestamp));
    }

    function getRecords(string memory _patientId) public view returns (Record[] memory) {
        return records[_patientId];
    }

    function addMedication(
        string memory _name,
        uint256 _dosage,
        uint256 _stock
    ) public onlyAdmin {
        medications[medicationCounter] = Medication(_name, _dosage, _stock);
        medicationCounter++;
    }

    function updateMedicationStock(uint256 _id, uint256 _newStock) public onlyAdmin {
        require(_id < medicationCounter, "Medication not found.");
        medications[_id].stock = _newStock;
    }

    function getMedications() public view returns (Medication[] memory) {
        Medication[] memory meds = new Medication[](medicationCounter);
        for (uint256 i = 0; i < medicationCounter; i++) {
            meds[i] = medications[i];
        }
        return meds;
    }
}
