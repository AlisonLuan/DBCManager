import cantools
import json
import csv
import subprocess

def load_dbc_file(file_path):
    """
    Load and parse a DBC file using cantools.
    
    :param file_path: Path to the DBC file.
    :return: Parsed DBC database object.
    """
    try:
        db = cantools.database.load_file(file_path)
        print(f"DBC file '{file_path}' loaded successfully.")
        return db
    except Exception as e:
        raise ValueError(f"Error loading DBC file: {e}")

def parse_dbc_file(db):
    """
    Parse the DBC file content into a structured format.

    :param db: Parsed DBC database object.
    :return: Dictionary representation of the DBC file content.
    """
    parsed_data = {
        "messages": [],
        "nodes": [],
    }

    # Extract node definitions
    for node in db.nodes:
        parsed_data["nodes"].append({
            "name": node.name,
            "comment": node.comment
        })

    # Extract message and signal definitions
    for message in db.messages:
        message_data = {
            "id": message.frame_id,
            "name": message.name,
            "length": message.length,
            "senders": message.senders,  # Extract transmitters for the message
            "signals": [],
            "comment": message.comment
        }

        for signal in message.signals:
            signal_data = {
                "name": signal.name,
                "start_bit": signal.start,
                "length": signal.length,
                "scaling": signal.scale,
                "offset": signal.offset,
                "unit": signal.unit,
                "multiplexer_signal": signal.multiplexer_signal,
                "multiplexer_ids": signal.multiplexer_ids,
                "receivers": signal.receivers,  # Extract receivers for the signal
                "comment": signal.comment
            }
            message_data["signals"].append(signal_data)

        parsed_data["messages"].append(message_data)

    return parsed_data

def display_node_selection(nodes):
    """
    Display available nodes and allow user to select one or more for analysis.

    :param nodes: List of nodes from the parsed DBC file.
    :return: List of selected nodes.
    """
    print("\nAvailable Nodes:")
    for i, node in enumerate(nodes, start=1):
        print(f"{i}. {node['name']}: {node['comment']}")

    while True:
        try:
            selected_indices = input("Enter the numbers corresponding to the nodes (comma-separated): ")
            selected_indices = [int(i) - 1 for i in selected_indices.split(',')]
            selected_nodes = [nodes[i]['name'] for i in selected_indices]
            return selected_nodes
        except (ValueError, IndexError):
            print("Invalid selection. Please try again.")

def generate_c_code_using_cantools(dbc_path, output_name=None, use_float=False, no_floating_point=False, node=None):
    """
    Generate C code from a DBC file using cantools.

    :param dbc_path: Path to the DBC file.
    :param output_name: Optional name for the output C header and source files.
    :param use_float: Use single precision floating point numbers (float).
    :param no_floating_point: Generate code without floating point types.
    :param node: Generate code for a specific node.
    """
    command = ["python3", "-m", "cantools", "generate_c_source", dbc_path]

    if output_name:
        command.extend(["--database-name", output_name])
    if use_float:
        command.append("--use-float")
    if no_floating_point:
        command.append("--no-floating-point-numbers")
    if node:
        command.extend(["--node", node])

    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error generating C code: {e.stderr}")

def save_to_json(data, output_path):
    """
    Save the parsed data to a JSON file.

    :param data: Parsed DBC data.
    :param output_path: Path to save the JSON file.
    """
    try:
        with open(output_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data successfully saved to {output_path}")
    except Exception as e:
        raise IOError(f"Error saving JSON file: {e}")

def save_to_csv(data, output_path):
    """
    Save the parsed data to a CSV file.

    :param data: Parsed DBC data.
    :param output_path: Path to save the CSV file.
    """
    try:
        with open(output_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)

            # Write message and signal headers
            writer.writerow(["Message ID", "Message Name", "Signal Name", "Start Bit", "Length", "Scaling", "Offset", "Unit"])
            for message in data["messages"]:
                for signal in message["signals"]:
                    writer.writerow([
                        message["id"],
                        message["name"],
                        signal["name"],
                        signal["start_bit"],
                        signal["length"],
                        signal["scaling"],
                        signal["offset"],
                        signal["unit"]
                    ])

        print(f"Data successfully saved to {output_path}")
    except Exception as e:
        raise IOError(f"Error saving CSV file: {e}")

def display_summary(data):
    """
    Display a summary of parsed data.

    :param data: Parsed DBC data.
    """
    print("\nSummary of DBC file:\n")
    print("Nodes:")
    for node in data["nodes"]:
        print(f"  - {node['name']}: {node['comment']}")

    print("\nMessages and Signals:")
    for message in data["messages"]:
        print(f"  Message ID: {message['id']} ({message['name']})")
        print(f"    Comment: {message['comment']}")
        for signal in message["signals"]:
            print(f"    Signal: {signal['name']} Start: {signal['start_bit']} Length: {signal['length']} Scaling: {signal['scaling']} Offset: {signal['offset']} Unit: {signal['unit']}")

if __name__ == "__main__":
    example_dbc_path = "example.dbc"
    output_json_path = "parsed_dbc.json"
    output_csv_path = "parsed_dbc.csv"

    try:
        # Load and parse the DBC file
        db = load_dbc_file(example_dbc_path)
        parsed_data = parse_dbc_file(db)

        # Allow node selection
        selected_nodes = display_node_selection(parsed_data["nodes"])

        # Generate C code using cantools
        for node in selected_nodes:
            generate_c_code_using_cantools(example_dbc_path, output_name=f"output_{node}", node=node)

        # Output results
        save_to_json(parsed_data, output_json_path)
        save_to_csv(parsed_data, output_csv_path)
        display_summary(parsed_data)
    except Exception as e:
        print(f"Error: {e}")
