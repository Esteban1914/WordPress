"""
    /* ====== v1.0.0 ====== /*
"""

from django.http import JsonResponse,HttpResponse
from django.db.utils import OperationalError

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

from .models import WordPress_TermTaxonomy,WordPress_TermRelationships,WordPress_Posts,WordPress_Terms

#!!!!   This improt need the excat address from settings.py !!!!
from wordpress.settings import DATABASES


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
        
        
"""Prueba de la funcion 'get_articles_by_categories' desde Django """
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
        return JsonResponse(list(response),safe=False)
   
    except Connection_DB_Error as cdb_error:
        print(cdb_error)
        return HttpResponse(cdb_error)
    