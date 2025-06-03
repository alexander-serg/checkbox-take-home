# Checkbox Service

## Assignment

You can find the detailed assignment in the separate file:  
[Assignment.docx](Assignment.docx)

## Requirements

- Docker Compose version **>= v2.30**  
  You can check your version with:
  ```bash
  docker compose version
  ```

## Setup

1. Create a `.env` file in the root of the project with the following variables:

   ```env
   HOST_URL=
   HOST_PORT=

   DATABASE_PORT=5432
   DATABASE_HOST=db
   DATABASE_USER=
   DATABASE_PASSWORD=
   DATABASE_NAME=

   AUTH_SECRET_KEY=
   ```

   - `AUTH_SECRET_KEY` can be generated with the following command:  
     ```bash
     openssl rand -hex 32
     ```
   - `HOST_URL` is usually `http://localhost/` if running locally.
   - `HOST_PORT` is the port your service will be accessible on.
   - `DATABASE_HOST` should be set to `db` since the Postgres service in Docker Compose is named `db`.

## Running the service

Run the following command to build and start the service with Docker Compose:

```bash
docker compose up --build
```

This will build the containers and start the application along with the Postgres database.

## Accessing the service

Once running, the service will be accessible at:

```
{HOST_URL}:{HOST_PORT}/
```
> Replace `{HOST_URL}` and `{HOST_PORT}` with your configured values from the `.env` file.

---
## API Specifications

You can find the detailed API specifications in the separate file:  
[API_Specifications.md](API_Specifications.md)

### Interactive API Docs

Access the interactive API documentation (Swagger UI) at:  
`{HOST_URL}:{HOST_PORT}/docs`

### Non-Interactive API Docs

Access the non-interactive API documentation (ReDoc) at:  
`{HOST_URL}:{HOST_PORT}/redoc`
