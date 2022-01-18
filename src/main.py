from genericpath import exists
import os.path
import os
from telnetlib import STATUS

from pydantic.errors import ConfigError
from markdownify import markdownify
from os import path
from slugify import slugify
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse

from models.article import Article
from typing import Optional
from jinja2 import Environment, FileSystemLoader

import json
import re

app = FastAPI(debug=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=[
        "POST",
        "GET",
        "DELETE",
        "PUT"
    ],
    allow_headers=["*"],
)


@app.get("/")
def home(): 
    return 

@app.post("/articles")
def create_article(article: Article):

    urls =re.findall(r"<a href='(wiki/.*?)\'\>*", article.content)
    
    if not len(urls) == 0:
        print("Duplicated values: ", urls)
        final_urls = list(dict.fromkeys(urls))
        urls = final_urls
        print("Not Duplicated values: ",final_urls)
        print("Panjang: ",len(urls))
        for x in urls:
            if os.path.exists(x):
                print("PATH FOUND !!")
                with open(x+"/index.json", "r") as a:
                    json_object = json.loads(a.read())
                print("JSON OBJECT in json_object: ", json_object["content"])
                print("CHECK IF " +x +" EXISTS IN JSON_OBJECT['OUTBOUND_LINKS']")
                if "wiki/"+article.title.lower()[0:3]+"/"+ slugify(article.title) in json_object["inbound_links"] :
                    print("VALUE ALREADY EXISTS")
                else:
                    json_object["inbound_links"].append("wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title))
                    open(x+"/index.json", "w").write(
                        json.dumps(json_object, indent=4, separators=(",", ":")))
            else:
                print("PATH "+x +" DOESN'T EXISTS")
    json_object = json.dumps(
        {
            "title":article.title,
            "content":article.content,
            "tags": article.tags,
            "inbound_links": [],
            "outbound_links": urls
        }, indent=4)
    
    first_path = path.exists("wiki/"+article.title[0:3])
    if first_path == False:
        pat = os.path.join("wiki",article.title.lower()[0:3])
        os.mkdir(pat)
    second_path = path.exists("wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title))
    if not second_path:
        pat = os.path.join("wiki/"+article.title.lower()[0:3],slugify(article.title))
        os.mkdir(pat)
    
    with open("latest/articles.json", "r") as a:
        latest_article = json.loads(a.read())
    latest_article['url'].append("wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title))
    print("Panjang",len(latest_article['url']))
    if(len(latest_article['url'])) >10:
        latest_article['url'].pop(0)
    open("latest/articles.json","w").write(
        json.dumps(latest_article, indent =4 , separators=(',',':'))
    )
    with open("wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title)+"/index.json", "w") as outfile:
        outfile.write(json_object)
    
    with open("latest/all.json", "r") as all:
        all_articles = json.loads(all.read())
    all_articles['url'].append("wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title))
    open("latest/all.json","w").write(
        json.dumps(all_articles, indent=4, separators=(',',':'))
    )
    
    for x in article.tags:
        first_tags_path = path.exists("tags/"+x.lower()[0:3])
        if first_tags_path == False:
            pat = os.path.join("tags", x.lower()[0:3])
            os.mkdir(pat)
        second_tags_path = path.exists("tags/"+x.lower()[0:3]+"/"+slugify(x))
        if not second_tags_path:
            pat = os.path.join("tags/"+x.lower()[0:3],slugify(x))
            os.mkdir(pat)
        
        tags_file_path = os.path.exists("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json")
        if tags_file_path:
            with open("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json", "r") as json_file:

                ember_bocor = json.loads(json_file.read())
            ember_bocor["url"].append(
                "wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title)
            )

            with open("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json", "w") as json_file:
                json.dump(ember_bocor, json_file, indent=4)
        if not tags_file_path:
            json_tags = json.dumps({
            "url" : [
                "wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title)
                ]
            }, indent= 4)
            print("EXISTENCE OF THE PATH: ",tags_file_path)
            print("Slugify: "+ slugify(x))
            with open("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json", "w") as file:
                file.write(json_tags)
        

    # with open("articles.json","r") as a:
    #     data = json.load(a)
    # for item in data:
    #     item["article"].append({"title":article.title,"content":article.content})
    # with open("articles.json","w") as a:
    #     json.dump(data, a, indent=4, separators=(',',':'))

    with open("wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title)+"/index.json", "r") as d :
        artikel = json.load(d)
    
    # with open("articles.json", "r") as d:
    #     an_article = json.load(d)
    # for item in article:
    #     get_articles = item['article']
    # an_article = get_articles

    fileLoader = FileSystemLoader("templates")
    env = Environment(loader=fileLoader)
    rendered = env.get_template("article.html").render(an_article=artikel, title="Gallery")

    with open("wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title)+"/index.html","w") as f:
        f.write(rendered)
    file = open("wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title)+"/index.html", "r").read()
    html = markdownify(file)

    with open("wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title)+"/index.md","w") as f:
        f.write(html)

@app.get("/articles")
def all_articles():
    with open("latest/all.json", "r") as all:
        all_articles = json.loads(all.read())
    return all_articles

@app.get("/articles/latest")
def latest_articles():
    with open("latest/articles.json", "r") as a:
        latest_article = json.loads(a.read())
    return latest_article

@app.get("/articles/wiki/{file_path:path}")
def read_article(file_path: str):
    
    with open("wiki/"+file_path+'/index.json') as JsonFile:
        data = json.loads(JsonFile.read())
    # return FileResponse("wiki/"+file_path+"/index.html")
    return {
        "title" : data['title'],
        "content" :data['content'],
        "tags": data['tags'],
        "inbound_links": data['inbound_links'],
        "outbound_links": data['outbound_links'],
    }

@app.put("/articles/wiki/{file_path:path}")
def update_article(file_path: str, article : Optional[Article]= None):
    new_urls = re.findall(r"<a href='(wiki/.*?)\'\>*", article.content)
    final_new_urls = list(dict.fromkeys(new_urls))
    new_urls = final_new_urls

    json_data = json.load(open("wiki/"+file_path+"/index.json"))
    old_urls = re.findall(r"<a href='(wiki/.*?)\'\>*", json_data["content"])
    final_old_urls = list(dict.fromkeys(old_urls))
    old_urls =final_old_urls

    for x in old_urls:
        print("X is: "+ x)
        print("JSON_DATA[OUTBOUND_LINKS]: ", json_data["outbound_links"])
        if x not in new_urls:
            print("X: "+x)
            json_data["outbound_links"].remove(x)
            open("wiki/"+file_path+"/index.json","w").write(
                json.dumps(json_data, indent= 4, separators=(",",":"))
            )
            inbound_remove = json.load(open(x+"/index.json"))
            inbound_remove["inbound_links"].remove("wiki/"+file_path)
            open(x+"/index.json","w").write(
                json.dumps(inbound_remove,indent=4, separators=(",",":"))
            )
    for x in new_urls:
        if os.path.exists(x):
            if x not in old_urls:
                json_data["outbound_links"].append(x)
                open("wiki/"+file_path+"/index.json", "w").write(
                    json.dumps(json_data, indent=4, separators=(",",":"))
                )
                inbound_add = json.load(open(x+"/index.json"))
                inbound_add["inbound_links"].append("wiki/"+file_path)
                open(x+"/index.json","w").write(
                    json.dumps(inbound_add, indent=4, separators=(",",":"))
                )

        else:
                print("PATH "+x +" DOESN'T EXISTS")


    print("NEW URLS: ", new_urls)
    print("OLD URLS: ", old_urls)

    print("Path:"+file_path)
    data = json.load(open("wiki/"+file_path+"/index.json"))
    print(data['tags'])
    # 
    for x in data['tags']:
        print("CHECK VALUE IF EXISTS")
        print(x in article.tags)
        if not x in article.tags:

            tags_remove = json.loads(open("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json").read())
            tags_remove["url"].remove("wiki/"+file_path)
            open("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json","w").write(
                json.dumps(tags_remove, indent =4 , separators=(',',':')))
    
            print(type(tags_remove))
            print("TAGS REMOVED")

    for x in article.tags:
        if not x in data['tags']:
            print(x+" DOESN'T EXISTS")
            first_tags_path = path.exists("tags/"+x.lower()[0:3])
            if first_tags_path == False:
                pat = os.path.join("tags", x.lower()[0:3])
                os.mkdir(pat)
            second_tags_path = path.exists("tags/"+x.lower()[0:3]+"/"+slugify(x))
            if not second_tags_path:
                pat = os.path.join("tags/"+x.lower()[0:3],slugify(x))
                os.mkdir(pat)
        
            tags_file_path = os.path.exists("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json")
            if tags_file_path:
                with open("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json", "r") as json_file:
                    ember_bocor = json.loads(json_file.read())
                ember_bocor["url"].append(
                    "wiki/"+article.title.lower()[0:3]+"/"+slugify(article.title)
                )
                with open("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json", "w") as json_file:
                    json.dump(ember_bocor, json_file, indent=4)
            if not tags_file_path:
                json_tags = json.dumps({
                    "url" : [
                        "wiki/"+file_path
                        ]
                    }, indent= 4)
                print("KEBERADAAN PATH : ",tags_file_path)
                with open("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json", "w") as file:
                    file.write(json_tags)

    data['title'] = article.title
    data['content'] = article.content
    data['tags'] = article.tags


    open("wiki/"+file_path+"/index.json","w").write(
        json.dumps(data, indent =4 , separators=(',',':')))
    
    with open("wiki/"+file_path+"/index.json", "r") as d :
        artikel = json.load(d)
    
    fileLoader = FileSystemLoader("templates")
    env = Environment(loader=fileLoader)
    rendered = env.get_template("article.html").render(an_article=artikel, title="Gallery")

    with open("wiki/"+file_path+"/index.html","w") as f:
        f.write(rendered)

    file = open("wiki/"+file_path+"/index.html", "r").read()
    html = markdownify(file)

    with open("wiki/"+file_path+"/index.md","w") as f:
        f.write(html)

@app.delete("/article/wiki/{file_path:path}")
def delete_article(file_path: str):
    
    ## Delete Path from related Inbound_Links in another files
    with open("wiki/"+file_path+"/index.json","r") as a:
        data = json.loads(a.read())
    for x in data["outbound_links"]:
        inbound_remove = json.loads(open(x+"/index.json").read())
        inbound_remove["inbound_links"].remove("wiki/"+file_path)
        open(x+"/index.json","w").write(
            json.dumps(inbound_remove, indent=4, separators=(',',":"))
        )
    ## End Delete

    ## Delete Path from latest.json
    with open("latest/articles.json", "r") as a:
        latest_article = json.loads(a.read())
    if "wiki/"+file_path in latest_article["url"]:
        latest_article['url'].remove("wiki/"+file_path)
    open("latest/articles.json","w").write(
    json.dumps(latest_article, indent =4 , separators=(',',':')))
    ## End of Delete Path from latest.json

    ## Delete Path from all.json
    with open("latest/all.json","r") as all:
        all_article = json.loads(all.read())
    if "wiki/"+file_path in all_article["url"]:
        all_article['url'].remove("wiki/"+file_path)
    open("latest/all.json","w").write(
        json.dumps(all_article, indent =4 , separators=(',',':'))
    )
    ## End of Delete Path from all.json
    
    ## Delete Path from TAGS
    data = json.load(open("wiki/"+file_path+"/index.json"))
    for x in data["tags"]:
        print(x)
        tags_remove = json.loads(open("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json").read())
        tags_remove["url"].remove("wiki/"+file_path)
        open("tags/"+x.lower()[0:3]+"/"+slugify(x)+"/index.json","w").write(
            json.dumps(tags_remove, indent =4 , separators=(',',':'))
        )
        print(type(tags_remove))
        print("TAGS REMOVED")
    ## End Delete Path from TAGS



    ## Delete JSON, MD and HTML File from Folder
    os.remove("wiki/"+file_path+"/index.json")
    os.remove("wiki/"+file_path+"/index.md")
    os.remove("wiki/"+file_path+"/index.html")
    ## End of Delete JSON, MD and HTML File from Folder
    return {
        "success": "200"
    }