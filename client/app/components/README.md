# Project Overview
====================

## Project Module
-----------------

This project is a modular software development framework designed to provide a structured approach to building scalable applications. The architecture is built using a microservices-based design, allowing for flexibility, modularity, and ease of maintenance.

## Project Goals
---------------

*   Provide a standardized framework for building software applications
*   Encourage modularity and reusability of code
*   Enable scalability and flexibility in application design
*   Foster a culture of maintainability and ease of use

## Setup
--------

### Prerequisites
-----------------

*   Java 17 or higher
*   Maven 3.8.6 or higher
*   Git 2.34.1 or higher

### Installation
----------------

1.  Clone the repository using Git: `git clone https://github.com/{username}/project-module.git`
2.  Navigate to the project directory: `cd project-module`
3.  Build the project using Maven: `mvn clean install`
4.  Run the project using Maven: `mvn spring-boot:run`

### Dependencies
----------------

*   Spring Boot 2.7.3
*   Spring Data JPA 2.7.3
*   Hibernate 5.6.7.Final
*   Apache Commons Lang3 3.12.0
*   Apache Commons IO 2.11.0

## Folder Structure
-------------------

### project-module
------------------

*   `src/main/java`
	+   `com.example.project.module`
		-   `domain`
		-   `repository`
		-   `service`
		-   `controller`
	+   `com.example.project.module.config`
		-   `DatabaseConfig.java`
		-   `SecurityConfig.java`
*   `src/main/resources`
	+   `application.properties`
	+   `application.yml`
*   `src/test/java`
	+   `com.example.project.module`
		-   `domain`
		-   `repository`
		-   `service`
		-   `controller`
	+   `com.example.project.module.config`
		-   `DatabaseConfigTest.java`
		-   `SecurityConfigTest.java`

## API Documentation
-------------------

### User API
--------------

#### GET /users
----------------

*   Retrieve a list of all users
*   **Method:** GET
*   **URL:** `/users`
*   **Response:**
	+   `200 OK`: List of users in JSON format
		-   `id` (integer)
		-   `name` (string)
		-   `email` (string)
	+   `404 NOT FOUND`: User not found
*   **Authorization:** None

#### GET /users/{id}
---------------------

*   Retrieve a user by ID
*   **Method:** GET
*   **URL:** `/users/{id}`
*   **Parameters:**
	+   `id` (integer): User ID
*   **Response:**
	+   `200 OK`: User in JSON format
		-   `id` (integer)
		-   `name` (string)
		-   `email` (string)
	+   `404 NOT FOUND`: User not found
*   **Authorization:** None

#### POST /users
----------------

*   Create a new user
*   **Method:** POST
*   **URL:** `/users`
*   **Request Body:**
	+   `name` (string)
	+   `email` (string)
*   **Response:**
	+   `201 CREATED`: User created in JSON format
		-   `id` (integer)
		-   `name` (string)
		-   `email` (string)
	+   `400 BAD REQUEST`: Invalid request
*   **Authorization:** None

#### PUT /users/{id}
---------------------

*   Update a user by ID
*   **Method:** PUT
*   **URL:** `/users/{id}`
*   **Parameters:**
	+   `id` (integer): User ID
*   **Request Body:**
	+   `name` (string)
	+   `email` (string)
*   **Response:**
	+   `200 OK`: User updated in JSON format
		-   `id` (integer)
		-   `name` (string)
		-   `email` (string)
	+   `404 NOT FOUND`: User not found
*   **Authorization:** None

#### DELETE /users/{id}
-----------------------

*   Delete a user by ID
*   **Method:** DELETE
*   **URL:** `/users/{id}`
*   **Parameters:**
	+   `id` (integer): User ID
*   **Response:**
	+   `204 NO CONTENT`: User deleted
	+   `404 NOT FOUND`: User not found
*   **Authorization:** None

### Project Documentation
-------------------------

#### Maven Dependencies
-----------------------

*   `spring-boot-starter-web`: Spring Boot Web Starter
*   `spring-boot-starter-data-jpa`: Spring Boot Data JPA Starter
*   `hibernate-core`: Hibernate Core
*   `commons-lang3`: Apache Commons Lang3
*   `commons-io`: Apache Commons IO

#### Configuration
-----------------

*   `application.properties`: Application configuration
*   `application.yml`: Application configuration

#### Security
------------

*   `SecurityConfig.java`: Security configuration
*   `DatabaseConfig.java`: Database configuration

## Commit Message Guidelines
---------------------------

*   Follow the Conventional Commits specification
*   Use the following format: `type(scope): subject`
*   `type`: One of the following:
	+   `feat`: A new feature
	+   `fix`: A bug fix
	+   `docs`: Documentation changes
	+   `style`: Changes to code style (formatting, etc.)
	+   `refactor`: Code refactoring
	+   `perf`: Performance improvements
	+   `test`: Adding tests
	+   `chore`: Changes to supporting files (e.g. .gitignore)
	+   `revert`: Revert a previous commit
*   `scope`: The scope of the commit (e.g. `auth`, `db`, etc.)
*   `subject`: A brief description of the commit