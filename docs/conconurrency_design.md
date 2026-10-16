### Server Concurrency Strategy

- **Architecture Choice:** Multithreading is the architecture of choice for this project's concurrency management. Threads are, in general, more straightforward than non-blocking socket select, with more precise management of behind-the-scenes processes (e.g. updating game state, validating questions, etc.). 

- **Synchronization Logic:** Explain how shared game state and client list are thread-safe (e.g. `threading.Lock`) to prevent race conditions during turn processing.