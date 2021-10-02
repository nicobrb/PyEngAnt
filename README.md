# PyEngAnt
Repository riguardante la rivisitazione in Python del modello client-server del progetto EngAnt, inizialmente ideata da Francesco Angarano.

Rielaborazione a cura di Nicola Barbaro, anno accademico 2020/2021 (Bari).

# Prima di iniziare

- Installare WSL2 seguendo questa guida:

    ```https://docs.microsoft.com/en-us/windows/wsl/install```


- Installare Docker Desktop:

    ```https://www.docker.com/products/docker-desktop```


- Clonare il progetto:

    ```git clone https://github.com/nicobrb/PyEngAnt.git```


- Creare l'ambiente virtuale:

    ```python -m venv PyEngAnt```


- Installare le dipendenze:

    ```cd PyEngAnt```

    ```pip install -r requirements.txt```

# Inizializzare il server

- Spostarsi sulla cartella del server:
    
    ```cd server```


- Assicurandosi di avere almeno un processo di Docker attivo, installare il server:

  ```docker build -t engflask .```


- Avviare il processo server:

  ```docker run --name engflaskserver -dp 8083:8083 -w /app engflask```

  *NB: il processo fallirà se è già presente un processo server chiamato engflaskserver in Docker.*


# Utilizzare il client

- Tornare alla cartella principale:
  
  ```cd ..```


- Eseguire lo script del client:

  ```python client/client.py```




         
