"""
                /* ====== v1.1.1 ====== /*
"""

""" From model.py
class WordPress_Posts(models.Model):
    id = models.BigAutoField(db_column='ID', primary_key=True)  # Field name made lowercase.
    post_title = models.TextField()
    class Meta:
        managed = False

class WordPress_TermRelationships(models.Model):
    object_id = models.PositiveBigIntegerField(primary_key=True)
    term_taxonomy_id = models.PositiveBigIntegerField()
    term_order = models.IntegerField()

    class Meta:
        managed = False
        unique_together = (('object_id', 'term_taxonomy_id'),)

class WordPress_TermTaxonomy(models.Model):
    term_taxonomy_id = models.BigAutoField(primary_key=True)
    term_id = models.PositiveBigIntegerField()
    taxonomy = models.CharField(max_length=32)
    class Meta:
        managed = False
        unique_together = (('term_id', 'taxonomy'),)

class WordPress_Terms(models.Model):
    term_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=200)
    
    class Meta:
        managed = False
"""

from django.http import JsonResponse,HttpResponse
from django.db.utils import OperationalError
from .models import WordPress_TermTaxonomy,WordPress_TermRelationships,WordPress_Posts,WordPress_Terms
from django.db.models import F
import re
#!!!!   This improt need the excat address from settings.py !!!!
from joomla.settings import DATABASES


#Exception 
class Connection_DB_Error(Exception):
    pass

def get_articles_by_categories(host:str,port:str,name:str,user:str,passw:str,prefix:str,categorys_title_list:list)->dict | str:
    try:
        #Update Database server info
        DATABASES.update(
            {
            'db_WordPress_mysql':
                {
                    'ENGINE': 'django.db.backends.mysql',
                    'HOST': host,
                    'PORT': port,
                    'NAME': name,
                    'USER': user,
                    'PASSWORD': passw,
                    'ATOMIC_REQUESTS': False,
                    'AUTOCOMMIT': True,
                    'CONN_MAX_AGE': 0,
                    'CONN_HEALTH_CHECKS': False, 
                    'OPTIONS': {},
                    'TIME_ZONE': None,
                    'TEST': {
                        'CHARSET': None,
                        'COLLATION': None,
                        'MIGRATE': True,
                        'MIRROR': None,
                        'NAME': None
                        },
                }
            }
        )
        #Update prefix  databases table
        WordPress_TermTaxonomy._meta.db_table=prefix + "term_taxonomy"
        WordPress_TermRelationships._meta.db_table=prefix + "term_relationships"
        WordPress_Posts._meta.db_table=prefix + "posts"
        WordPress_Terms._meta.db_table=prefix + "terms"
        
        #Get Ids Categories from DB
        ids_terms_categories=WordPress_Terms.objects.using("db_WordPress_mysql").filter(name__in=categorys_title_list).values_list('term_id',flat=True)
        if ids_terms_categories:
            #Get Ids Categorys Taxonomy from DB
            ids_taxonomy_categories= WordPress_TermTaxonomy.objects.using("db_WordPress_mysql").filter(term_id__in=ids_terms_categories,taxonomy="category").values_list("term_taxonomy_id",flat=True)
            
            if ids_taxonomy_categories:
                #Get Posts id into Relationship table from DB
                ids_post_relationships=WordPress_TermRelationships.objects.using("db_WordPress_mysql").filter(term_taxonomy_id__in=ids_taxonomy_categories).values_list("object_id",flat=True)
        
                if ids_post_relationships:
                    posts=WordPress_Posts.objects.using("db_WordPress_mysql").filter(id__in=ids_post_relationships).values('id','post_title')
        
                    if posts:
                        #Verify conections errors
                        return posts
                    else:
                        error="Error (3)"
                else:
                    error="Error (2)"
            else:
                error="Error (1)"
        else:
            error="Error (0)"    
            
    except ValueError as ve:
        error="Error, la lista de entrada tiene un formato incorrecto; Error:{}".format(ve)
    except OperationalError as oe:
        error="Error, no se ha podido conectar a la base de datos; Error:{}".format(oe)
    except Exception as e:
        error="Error desconocido; Error:{}".format(e)
    raise Connection_DB_Error(error)
        
def set_tag_to_articles(host:str,port:str,name:str,user:str,passw:str,prefix:str,articles_title_id_tagTitleList_dict:dict)->str:
    try:
        
        #Update Database server info
        DATABASES.update(
            {
            'db_WordPress_mysql':
                {
                    'ENGINE': 'django.db.backends.mysql',
                    'HOST': host,
                    'PORT': port,
                    'NAME': name,
                    'USER': user,
                    'PASSWORD': passw,
                    'ATOMIC_REQUESTS': False,
                    'AUTOCOMMIT': True,
                    'CONN_MAX_AGE': 0,
                    'CONN_HEALTH_CHECKS': False, 
                    'OPTIONS': {},
                    'TIME_ZONE': None,
                    'TEST': {
                        'CHARSET': None,
                        'COLLATION': None,
                        'MIGRATE': True,
                        'MIRROR': None,
                        'NAME': None
                        },
                }
            }
        )
        #Update prefix  databases table
        WordPress_TermTaxonomy._meta.db_table=prefix + "term_taxonomy"
        WordPress_TermRelationships._meta.db_table=prefix + "term_relationships"
        WordPress_Posts._meta.db_table=prefix + "posts"
        WordPress_Terms._meta.db_table=prefix + "terms"  

        response_python={"error_id":"","error":"","response":""}
        
        for article in articles_title_id_tagTitleList_dict:
            #Verif obfect_id exist
            object_id=WordPress_Posts.objects.using("db_WordPress_mysql").filter(id=article.get("id")).values_list("id",flat=True).first()
            if not object_id:
                #If not exist error  
                response_python["error_id"]+="{}".format(article.get("id"))
                continue
            #For show id in response
            show_id=True
            
            
            for title in article.get("tags_title"):

                #Format for slug
                title_slug=re.sub('[^A-Za-z0-9]+', '',title)
                title_slug=title_slug.lower()
                title_slug=title_slug.replace(" ","-")
                
                created=False
                ok=False
                #Find Tag id into term table
                term_id=WordPress_Terms.objects.using("db_WordPress_mysql").filter(name=title).values_list("term_id",flat=True).first()
                if not term_id:
                    #if no exist ,create it
                    new_term=WordPress_Terms.objects.using("db_WordPress_mysql").create(name=title,slug=title_slug,term_group=0)
                    term_id=new_term.term_id
                    if not term_id:
                        response_python["error"]+="{} (0)".format(title)
                        continue
                    ok=True
                    created=True
                
                #Find taxonomy tag into taxonomy table
                term_taxonomy_id=WordPress_TermTaxonomy.objects.using("db_WordPress_mysql").filter(term_id=term_id).values_list("term_taxonomy_id",flat=True).first()
                if not term_taxonomy_id:
                    #if no exist ,create it
                    new_term_taxonomy=WordPress_TermTaxonomy.objects.using("db_WordPress_mysql").create(term_id=term_id,taxonomy="post_tag",parent=0,count=0)
                    term_taxonomy_id=new_term_taxonomy.term_taxonomy_id
                    if not term_taxonomy_id:
                        response_python["error"]+="{} (1)".format(title)
                        continue
                    ok=True
                
                #Find relationships into relationship table
                relationship=WordPress_TermRelationships.objects.using("db_WordPress_mysql").filter(term_taxonomy_id=term_taxonomy_id,object_id=object_id).exists()
                if not relationship:
                    #if no exist ,create it
                    new_relationship=WordPress_TermRelationships.objects.using("db_WordPress_mysql").create(object_id=object_id,term_taxonomy_id=term_taxonomy_id,term_order=0)
                    if not new_relationship:
                        response_python["error"]+="{} (2)".format(title)
                        continue
                    #Update Count of posts with this tag 
                    upd=WordPress_TermTaxonomy.objects.using("db_WordPress_mysql").filter(term_id=term_id,term_taxonomy_id=term_taxonomy_id).update(count=F("count")+1)
                    if not upd:
                        response_python["error"]+="{} (3)".format(title)
                        continue 
                    ok=True
                #If ok == true somesing is add into tables
                if ok:
                    #For show id of post first ( logg )
                    if show_id==True:
                        show_id=False
                        response_python["response"]+="[{}],".format(object_id)
                    
                    response_python["response"]+="{} {}".format(title,"(+)," if created==True else "(-),")
    
    
    except Exception as e:
        response_python["error"]="Ha ocurrido un error:{}".format(e)
    
    if response_python["response"]:
        response_python["response"]="Tags Correctos: {}".format(response_python["response"])
    
    if response_python["error"]:
        response_python["error"]="Tags Fallidos: {}".format(response_python["error"])
    
    if response_python["error_id"]:
        response_python["error_id"]="IDs inexistente:  {}".format(response_python["error_id"])
    
    return response_python    
            
            
"""Test functin 'get_articles_by_categories' and 'set_tag_to_articles' from Django"""
def HomeView(request):
    names=["Category1","Category2","Category3"]
    try:
        response=get_articles_by_categories(
            host="127.0.0.1",
            port="3306",
            name="wordpress",
            user="root",
            passw="",
            prefix="wp_",
            categorys_title_list=names,
            )
        #Insert list of titles of Tags in each element , insert into list ["tags_title"] all Tags Titles 
        for resp in response:
            resp["tags_title"]=["Tag1","Tag2","Tag3","Táag4","Tag!?/+_?- !@ #  $%^@#5","tag6"]

        response=set_tag_to_articles(
            host="127.0.0.1",
            port="3306",
            name="wordpress",
            user="root",
            passw="",
            prefix="wp_",
            articles_title_id_tagTitleList_dict=response,
        )

        return JsonResponse(dict(response),safe=False)
   
    except Connection_DB_Error as cdb_error:
        print(cdb_error)
        return HttpResponse(cdb_error)
    
    