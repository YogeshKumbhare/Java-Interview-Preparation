import os, re, json, requests
base_dir = r'c:\Users\yoges\Downloads\Rag\Java-Interview-Prep\12-System-Design\ByteByteGo-SDI'
images_dir = os.path.join(base_dir, 'images')

for file in os.listdir(base_dir):
    if file.endswith('.md') and file[0].isdigit():
        chapter = re.match(r'^(\d+)', file).group(1)
        if int(chapter) < 20: continue
        ch_dir = os.path.join(images_dir, f'ch{chapter}')
        filepath = os.path.join(base_dir, file)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        slug = re.sub(r'^\d+-', '', file).replace('.md', '').lower()
        topic_url = f'https://bytebytego.com/courses/system-design-interview/{slug}'
        print(f'Processing {file} -> {topic_url}')

        try:
            resp = requests.get(topic_url, timeout=10)
            if resp.status_code != 200: continue
            next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text)
            if not next_data_match: continue
            next_data = json.loads(next_data_match.group(1))
            code_str = next_data.get('props', {}).get('pageProps', {}).get('code', '')
            img_urls = re.findall(r'"(/images/courses/[^"]+\.(?:png|svg|jpg))"', code_str)
            img_urls = list(dict.fromkeys(img_urls))
            if not img_urls: continue
            os.makedirs(ch_dir, exist_ok=True)
            for index, img_path in enumerate(img_urls):
                full_url = 'https://bytebytego.com' + img_path
                ext = img_path.split('.')[-1]
                fig_match = re.search(r'figure(?:-\d+)?-(\d+)', img_path, re.IGNORECASE)
                if fig_match:
                    fig_num = fig_match.group(1)
                    local_filename = f'figure-{fig_num}.{ext}'
                else:
                    local_filename = f'figure-{index+1}.{ext}'
                local_filepath = os.path.join(ch_dir, local_filename)
                if not os.path.exists(local_filepath) or os.path.getsize(local_filepath) == 0:
                    img_resp = requests.get(full_url)
                    with open(local_filepath, 'wb') as img_f:
                        img_f.write(img_resp.content)
                if fig_match:
                    content = re.sub(rf'images/ch{chapter}/figure-{fig_num}\.(png|svg|jpg)', f'images/ch{chapter}/figure-{fig_num}.{ext}', content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f'Error: {e}')
print("Done chapters 20-30")
