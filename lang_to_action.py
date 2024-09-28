

def language_to_action(input_language, obs_tree):
    print(obs_tree)
    if input_language == "click":
        match = re.search(r"\[(\d+)\] textbox 'Search GitLab' required: False", obs_tree).group(1)
        click_action = create_id_based_action(f"click [{match}]")
        return click_action
    else:
        match = re.search(r"\[(\d+)\] searchbox 'Search GitLab'", obs_tree).group(1)
        click_action = create_id_based_action(f"type [{match}] [machine learning] [0]")
        return click_action
if __name__ == "__main__":
    import re
    from dotenv import load_dotenv
    import os
    from browser_env import (
        Action,
        ActionTypes,
        ObservationMetadata,
        ScriptBrowserEnv,
        StateInfo,
        Trajectory,
        action2str,
        create_id_based_action,
        create_stop_action,
    )
    from PIL import Image
    load_dotenv() 
    api_key = os.getenv('OPENAI_API_KEY')
    env = ScriptBrowserEnv(
        headless=True,
        slow_mo=100,
        observation_type="accessibility_tree",
        current_viewport_only=True,
        viewport_size={"width": 1280, "height": 720},
    )

    config_file = "config_files/156.json"
    obs, info = env.reset(options={"config_file": config_file})
    actree_obs = obs["text"]
    step = 0
    img_obs = obs["image"]
    image = Image.fromarray(img_obs)
    image.save(f'images/step{step}.png')
    utterance_list = ["click", "type"]
    for utterance in utterance_list:
        action = language_to_action(utterance, actree_obs)
        obs, _, terminated, _, info = env.step(action)
        actree_obs = obs["text"]
        step += 1
        img_obs = obs["image"]
        image = Image.fromarray(img_obs)
        image.save(f'images/step{step}.png')
    print(obs["text"])