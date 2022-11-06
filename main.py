from subprocess import Popen

def kill_processes(procs: dict):
    try:
        print()
        while True:
            user_input = input("")
            if user_input.lower() == "quit":
                break
            else:
                continue
    except KeyboardInterrupt:
        print("User interrupted")
    finally:
        # Either way we want to kill the processes
        for k in procs:
            procs[k].kill()


# Entry point
if __name__ == '__main__':

    main_server = {
        "https_redirect": Popen(['python3', '-m', 'https_redirect']), # start the redirect process
        "server": Popen(['python3', '-m', 'server']) # start the main process
    }

    for k in main_server:
        print(f"Subprocess {k} running on PID: {main_server[k].pid}")

    kill_processes(main_server)