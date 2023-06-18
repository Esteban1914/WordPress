<?php

/* ====== v1.0.1 ====== /*

/*****
 *
 * NOTA IMPORTANTE
 *
 * El fichero base de carga de contenidos debe estar en UTF-8 sin BOM
 *
 *
 */

 /* Format in articolo.txt
    
    SET_TAG| id_article
    TAG_TITLE| tag_name
    TAG_TITLE| tag_name2

 */
/****  VARs  *******/
$response_python["error_id"]=array();
$response_python["error"]=array(); 
$response_python["response"]=array(); 
$date = date ('Y-m-d H:m:s');
$recortes = file("articolo.txt",  FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
$base_de_datos = file("base_de_datos.txt",  FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
$data=null;
$article_id=null;
$term_id=null;
$term_taxonomy_id=null;
$ok=null;
$show_id=null;
$result=null;
$created=null;

error_reporting(E_ERROR);

function remove_utfo_bom($text){
    $bom = pack('H*','EFBBBF');
    $text = preg_replace("/^$bom/",'',$text);
    return $text;
}
function quitar_acentos($cadena){
    $originales = 'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûýýþÿ';
    $modificadas = 'aaaaaaaceeeeiiiidnoooooouuuuybsaaaaaaaceeeeiiiidnoooooouuuyyby';
    $cadena = utf8_decode($cadena);
    $cadena = strtr($cadena, utf8_decode($originales), $modificadas);
    $textoLimpio = preg_replace('([^A-Za-z0-9 -])', '', $cadena);
    return utf8_encode($textoLimpio);
}
//Search info DB from txt File 
foreach ($base_de_datos as $ind=>$value) {
    
    $line1 = explode("^/^^/^", $value);

    $line1[0] = remove_utfo_bom($line1[0]);
    switch (true) {
        case preg_match("/^HOST/", $line1[0]):
            $host = trim($line1[1]);
            break;
        case preg_match("/^USER/", $line1[0]):
            $user = trim($line1[1]);
            break;
        case preg_match("/^PASSWORD/", $line1[0]):
            $password  = trim($line1[1]);
            break;
        case preg_match("/^DATABASE/", $line1[0]):
            $database = trim($line1[1]);
            break;
        case preg_match("/^URL/", $line1[0]):
            $URL = trim($line1[1]);
            break;
        case preg_match("/^PREFIJO/", $line1[0]):
            $prefix_table = trim($line1[1]);
            break;
        default;
            break;
    }
}

//Fill Tables Prefix
$table_posts = $prefix_table.'posts';
$table_terms = $prefix_table.'terms';
$table_term_taxonomy = $prefix_table.'term_taxonomy';
$table_term_relationships = $prefix_table.'term_relationships';

//Init Connection DB
$mysqli = new mysqli($host,$user,$password,$database); 

if ($mysqli->connect_error)
{
    $response_python["error"] = "Error al conectarse a la base de datos: $mysqli->connect_error";
    die(json_encode($response_python));
}

//Search instructions from txt file
foreach ($recortes as $ind=>$value) 
{
    $line = explode("|", $value);
    $line[0] = remove_utfo_bom($line[0]);
    switch (true) 
    {
        case preg_match("/^SET_TAG/", $line[0]):
            $article_id = trim($line[1]);
            $result=$mysqli->query("SELECT 1 FROM $table_posts WHERE ID = $article_id ");
            if ($result->num_rows <= 0) 
            {   
                //No exists
                array_push($response_python["error_id"],$article_id);
                $article_id=null;
                $show_id=null;
                break;
            } 
            $show_id=true;
        break;

        case preg_match("/^TAG_TITLE/", $line[0]):
           
            if($article_id != null)
            {
                $tag_title=trim($line[1]);
                
                //Verify tag exists    
                $result = $mysqli->query("SELECT term_id FROM $table_terms WHERE name='$tag_title'");
                
                $created=False;
                $ok=False;
                if ($result->num_rows <= 0) 
                {   
                    //If no exist tag, create it     
                    
                    //Format to slug
                    $tag_title_lnh=quitar_acentos($tag_title);
                    $tag_title_lnh=strtolower($tag_title_lnh);
                    $tag_title_lnh= str_replace(' ', '-', $tag_title_lnh);               
                   
                    //Insert Term
                    $result=$mysqli->query("INSERT INTO $table_terms (`name`,`slug`,`term_group`)  VALUES ('$tag_title','$tag_title_lnh',0) ;");
                    
                    if( ! $result)
                    {
                        array_push($response_python["error"], $tag_title." (0)->$mysqli->error");
                        break;
                    }
                    //Select new term id
                    $result=$mysqli->query("SELECT max(term_id) as term_id from $table_terms");

                    if ($result->num_rows <= 0) 
                    {
                        array_push($response_python["error"], $tag_title." (1)");
                        break;
    
                    }

                    $created=true;
                    $ok=true;
                }
                
                //Get Term ID 
                $data=$result->fetch_object();
                $term_id=$data->term_id;
                
                //Verify Taxonomy  
                $result=$mysqli->query("SELECT term_taxonomy_id from $table_term_taxonomy WHERE term_id=$term_id");

                if ($result->num_rows<=0)
                {
                    //If dont exists , create 
                    $result=$mysqli->query("INSERT INTO $table_term_taxonomy (`term_id`,`taxonomy`,`parent`,`count`)  VALUES ($term_id,'post_tag',0,0) ;");
                    if (! $result)
                    {
                        array_push($response_python["error"], $tag_title." (2)->$mysqli->error");
                        break;
                    }

                    //select new taxonomy id
                    $result=$mysqli->query("SELECT max(term_taxonomy_id) as term_taxonomy_id from $table_term_taxonomy");
                    if ($result->num_rows <= 0) 
                    {
                        array_push($response_python["error"], $tag_title." (3)");
                        break;
                    }
                    
                    $ok=true;
                }
                //Get Term Taxonomy id 
                $data=$result->fetch_object();
                $term_taxonomy_id=$data->term_taxonomy_id;
                
                
                
                //Verifiy relationships
                $result=$mysqli->query("SELECT 1  from $table_term_relationships WHERE term_taxonomy_id=$term_taxonomy_id AND object_id=$article_id");

                if ($result->num_rows<=0)
                {
                    //Insert  Relationship
                    $result=$mysqli->query("INSERT INTO $table_term_relationships (`object_id`,`term_taxonomy_id`,`term_order`) VALUES ($article_id,$term_taxonomy_id,0) ;");
                    if (! $result)
                    {
                        array_push($response_python["error"], $tag_title." (4)->$mysqli->error");
                        break;
                    }

                    //Update Count Tag relationsips
                    $result=$mysqli->query("UPDATE $table_term_taxonomy SET count=count+1 where term_taxonomy_id=$term_taxonomy_id AND term_id=$term_id;");
                    if( ! $result)
                    {                
                        array_push($response_python["error"],$tag_title." (5)->$mysqli->error");
                        break;
                    }
                

                    $ok=true;
                }

                if ($ok==true)
                {
                    if ($show_id==true)
                    {
                        array_push($response_python["response"],"[$article_id]");
                        $show_id=false;
                    }
                    array_push($response_python["response"],$tag_title .($created==true ? " (+)" : " (-)"));
                    
                }
            }
            break;
    }
}

$mysqli->close();

if (count($response_python['response']) > 0)
    $response_python['response'] = "Tags Correctos: ".implode(',',$response_python['response']);
if (count($response_python['error']) > 0)
    $response_python['error'] = "Tags Fallidos: ".implode(',',$response_python['error']);
if (count($response_python['error_id']) > 0)
    $response_python['error_id'] = "IDs inexistente: ".implode(',',$response_python['error_id']);

exit(json_encode($response_python));

?>