import os
import re
import json
import requests
import shutil

base_dir = r"c:\Users\yoges\Downloads\Rag\Java-Interview-Prep\12-System-Design\ByteByteGo-SDI"
images_dir = os.path.join(base_dir, "images")

if not os.path.exists(images_dir):
    os.makedirs(images_dir)

for file in os.listdir(base_dir):
    if file.endswith(".md") and file[0].isdigit():
        chapter_match = re.match(r'^(\d+)', file)
        if not chapter_match:
            continue
        chapter = chapter_match.group(1)
        ch_dir = os.path.join(images_dir, f"ch{chapter}")
        
        # Check if already has some files, but maybe we should just ensure all images are fetched
        # Let's read the markdown file
        filepath = os.path.join(base_dir, file)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        source_match = re.search(r'Source:\s*\[.*?\]\((https://bytebytego.com/courses/system-design-interview/[^\)]+)\)', content)
        if not source_match:
            print(f"No source URL found for {file}")
            continue
            
        topic_url = source_match.group(1)
        
        print(f"Processing {file} -> {topic_url}")
        
        try:
            resp = requests.get(topic_url, timeout=10)
            if resp.status_code != 200:
                print(f"Failed to fetch {topic_url}")
                continue
                
            # Extract NEXT_DATA from html
            next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text)
            if not next_data_match:
                print(f"No NEXT_DATA found for {topic_url}")
                continue
                
            next_data = json.loads(next_data_match.group(1))
            code_str = next_data.get('props', {}).get('pageProps', {}).get('code', '')
            
            # Extract all image paths in the code block
            # Pattern like "/images/courses/system-design-interview/google-maps/figure-xx-YYY.png"
            # It could also be named something else. But they typically contain "/images/courses/"
            img_urls = re.findall(r'"(/images/courses/[^"]+\.(?:png|svg|jpg))"', code_str)
            
            # Deduplicate while preserving order
            img_urls = list(dict.fromkeys(img_urls))
            
            if not img_urls:
                print(f"No images found in page code for {file}")
                # Some chapters realistically don't have images
                continue
                
            os.makedirs(ch_dir, exist_ok=True)
            
            # Now download the images
            # But wait, how do we name them? The ByteByteGo names are like 'figure-9-1-SY5VC26X.png'
            # The markdown might already have 'figure-1.png'
            # Let's just download them as figure-1.ext, figure-2.ext in order, but it's tricky because the order in `code_str` might just be a set of variable declarations at the top.
            # Yes, usually it's variables at the top in the order they are used, or just sorted.
            # Even better, the variables are assigned, e.g. A="/images/...", and then used in the AST. 
            # So downloading them and rewriting the file's image links to match isn't super safe unless we are sure of the order.
            
            # Let's see if the markdown has ![(...)](images/chXX/...)
            images_in_md = re.findall(r'!\[.*?\]\((images/ch[0-9]+/[^)]+)\)', content)
            
            # Instead of guessing the order perfectly, let's map the images based on the 'figure-X' pattern in their filename!
            # Example: 'figure-9-1-SY5VC26X.png' -> likely figure 1 of the chapter
            # Example: 'google-maps-3.png' -> figure 3 ?
            
            downloaded_files = {}
            for index, img_path in enumerate(img_urls):
                full_url = "https://bytebytego.com" + img_path
                ext = img_path.split('.')[-1]
                
                # try to parse figure number from string like figure-9-4 or figure-4
                fig_match = re.search(r'figure(?:-\d+)?-(\d+)', img_path, re.IGNORECASE)
                if fig_match:
                    fig_num = fig_match.group(1)
                    local_filename = f"figure-{fig_num}.{ext}"
                else:
                    # fallback to sequential
                    local_filename = f"figure-{index+1}.{ext}"
                    
                local_filepath = os.path.join(ch_dir, local_filename)
                
                # Only download if we don't have it (or if it's 0 bytes)
                if not os.path.exists(local_filepath) or os.path.getsize(local_filepath) == 0:
                    print(f"Downloading {full_url} to {local_filepath}")
                    img_resp = requests.get(full_url)
                    with open(local_filepath, "wb") as img_f:
                        img_f.write(img_resp.content)
                        
                # Update Markdown file: Replace any images/ch{chapter}/figure-{fig_num}.png or .svg with the actual ext
                if fig_match:
                    # Replace anything like figure-4.png or figure-4.svg with the correct extension
                    content = re.sub(rf'images/ch{chapter}/figure-{fig_num}\.(png|svg|jpg)', f'images/ch{chapter}/figure-{fig_num}.{ext}', content)

            # Write the updated content back
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
                
        except Exception as e:
            print(f"Error on {file}: {e}")

print("Done processing all topics.")
