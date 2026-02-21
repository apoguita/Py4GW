import re

with open(r'c:\Users\Damir\Desktop\Py4GW Apoguita-Moj unlock chest\Py4GW\Sources\oazix\CustomBehaviors\start_drop_viewer.py', 'r') as f:
    text = f.read()

new_block = """            # Get ALL active messages and filter for ours
            messages = shmem.GetAllMessages()
            for msg_idx, shared_msg in messages:
                if shared_msg.ReceiverEmail != my_email:
                    continue
                    
                if shared_msg.Command != 25: # SharedCommandType.CustomBehaviors is 25
                    continue
                    
                is_tracker_message = False
                try:
                    extra_data_list = shared_msg.ExtraData
                    if len(extra_data_list) == 0:
                        continue
                        
                    extra_0 = _c_wchar_array_to_str(extra_data_list[0])
                    if extra_0 != "TrackerDrop":
                        # Do not consume messages owned by other subsystems.
                        continue
                    
                    is_tracker_message = True

                    item_name = _c_wchar_array_to_str(extra_data_list[1]) if len(extra_data_list) > 1 else "Unknown Item"
                    exact_rarity = _c_wchar_array_to_str(extra_data_list[2]) if len(extra_data_list) > 2 else "Unknown"
                    display_time = _c_wchar_array_to_str(extra_data_list[3]) if len(extra_data_list) > 3 else ""
"""

# replace between "for _ in range(20):" and "quantity_param ="
pattern = r'# Read max 20 messages per tick to prevent hanging.*?exact_rarity = _c_wchar_array_to_str\(extra_data_list\[2\]\).*?else ""'
text = re.sub(pattern, new_block, text, flags=re.DOTALL)

with open(r'c:\Users\Damir\Desktop\Py4GW Apoguita-Moj unlock chest\Py4GW\Sources\oazix\CustomBehaviors\start_drop_viewer.py', 'w') as f:
    f.write(text)

print("success")
