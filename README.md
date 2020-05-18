# PS-VulcaNet

Processo Seletivo VulcaNet

## Running the docker image

```bash
docker login

docker pull steckhelena/queue_manager.py:release
docker pull steckhelena/cmd_interpreter.py:release

# Run the server
docker run -p 5678:5678 --rm --name queue_manager -it -d steckhelena/queue_manager.py:release

# Run the client in an interactive terminal
docker run --net="host" --rm --name cmd_client -it steckhelena/cmd_interpreter.py:release

# To see available commands type in `help` in the client terminal
```
