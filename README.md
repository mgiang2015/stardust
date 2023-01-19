# Stardust - Trace-based cache coherence simulator

Stardust is a trace-based simulator for cache coherence protocols MESI and Dragon. The name Stardust came from the card Stardust Dragon from Yu-Gi-Oh trading card game. This is Assignment 2 of CS4223 Multi-core Architectures, which I took in Semester 1 AY2022-23.

## What is it?

Stardust is a trace-based simulator for 2 cache coherence protocol covered in CS4223: Dragon and MESI. An optimisation of MESI protocol, which is MOESI protocol, has been implemented as well.

Stardust traces files with the following specification:
- Ends with `.data`
- For multiple cores: `traceFileName_0.data`, `traceFileName_1.data`, ... The number indicates which core this trace file should be run on.
- Each line contains 2 values separated by a space: `Label HexValue`. For example, `0 0x817b08`
- For `Label`, `0` is a load / read, `1` is a store / write, `2` is other instructions (computational instructions).
- For `HexValue`, For load (`0`) and store (`1`) instructions, value indicates the effective address of the memory word to be accessed by the core, while for other instructions (2), value denotes clock cycles required by other instructions between two memory access operations (load/store instructions)

## Simulation implementation

Each computer system has multiple cores, each core has its own cache (only L1 cache in this simulator) and different caches communicate via a snoop-based bus.

I modelled each component with a class (`system`, `core`, `cache` and `bus`) and initialise instances according to the parameters given via command line. There is a `tracker` component which keeps track of time elapsed (in cycles) along with other useful statistics.

For each line in the trace file:
- `system` parses the label and value to call the corresponding handler in the core.
- `core` invokes the handler in `cache` if the instruction is read or write. If it is other instructions (2) instead, it simply invokes the handler in `tracker`.
- Depending on the current state and availability of cache line, `cache` will either update its state or send a request to `bus` via `core`.
- `bus` has access to all the caches and is able to update / invalidate cache lines in remote caches based on the request given.
- After all operations has completed, `tracker` updates its statistics based on which operations were carried out.

## Running the program

1. Clone this repo and go into the repository

`git clone https://github.com/mgiang2015/stardust && cd stardust/`

2. Run the program

`python3 main.py "protocol" "input_file" "cache_size" "associativity" "block_size"`

For example

`python3 main.py MESI traces/mock_0.data 4096 2 16`

3. Results are written to a separate file