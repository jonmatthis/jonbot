import json
from copy import deepcopy
from pathlib import Path


def save_all_results_to_markdown(all_results: dict,
                                 directory_root: str,
                                 index_type: str):
    root_path = Path(directory_root)
    for index_id, index_type_results in all_results.items():
        if not isinstance(index_type_results, dict):
            raise ValueError(f"Expected index_type_results to be a dict, but got {type(index_type_results)}")

        for results_source, index_name_results in index_type_results.items():
            result_save_path = root_path / f"extraction_by_{index_type_in}" / index_id.replace(":",
                                                                                               "_") / results_source
            result_save_path.mkdir(parents=True, exist_ok=True)
            markdown_string = ""
            file_name = f"{index_id}__{results_source}.md".replace(":", "_")
            markdown_string += f"# {file_name}\n\n"

            markdown_file_path = result_save_path / file_name
            for input_output, result_str in index_name_results.items():
                markdown_string += f"## {input_output}\n\n"
                markdown_string += result_str
                markdown_string += "\n\n___\n\n"
            markdown_file_path.write_text(markdown_string, encoding="utf-8")


if __name__ == "__main__":
    # all_results_json_path = r"C:\Users\jonma\syncthing_folders\jon_main_syncthing\jonbot_data\classbot_database\classbot_chats_by_chat_id_2023-10-31_analysis_by_channel.json"
    all_results_json_path = r"C:\Users\jonma\syncthing_folders\jon_main_syncthing\jonbot_data\classbot_database\classbot_chats_by_chat_id_2023-10-31_analysis_by_category.json"
    save_path = r"C:\Users\jonma\syncthing_folders\jon_main_syncthing\teaching_stuff\neural_control_of_real_world_human_movement\2023-09-Fall\docs\ObsidianVault"

    all_results_in = json.loads(Path(all_results_json_path).read_text(encoding="utf-8"))[0]
    del all_results_in["_id"]
    del all_results_in["server_id"]
    index_type_in = deepcopy(all_results_in["index_type"])
    del all_results_in["index_type"]
    save_all_results_to_markdown(all_results=all_results_in, directory_root=save_path, index_type=index_type_in)
