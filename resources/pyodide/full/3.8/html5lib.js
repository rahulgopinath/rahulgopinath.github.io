var Module=typeof pyodide._module!=="undefined"?pyodide._module:{};Module.checkABI(1);if(!Module.expectedDataFileDownloads){Module.expectedDataFileDownloads=0;Module.finishedDataFileDownloads=0}Module.expectedDataFileDownloads++;(function(){var loadPackage=function(metadata){var PACKAGE_PATH;if(typeof window==="object"){PACKAGE_PATH=window["encodeURIComponent"](window.location.pathname.toString().substring(0,window.location.pathname.toString().lastIndexOf("/"))+"/")}else if(typeof location!=="undefined"){PACKAGE_PATH=encodeURIComponent(location.pathname.toString().substring(0,location.pathname.toString().lastIndexOf("/"))+"/")}else{throw"using preloaded data can only be done on a web page or in a web worker"}var PACKAGE_NAME="html5lib.data";var REMOTE_PACKAGE_BASE="html5lib.data";if(typeof Module["locateFilePackage"]==="function"&&!Module["locateFile"]){Module["locateFile"]=Module["locateFilePackage"];err("warning: you defined Module.locateFilePackage, that has been renamed to Module.locateFile (using your locateFilePackage for now)")}var REMOTE_PACKAGE_NAME=Module["locateFile"]?Module["locateFile"](REMOTE_PACKAGE_BASE,""):REMOTE_PACKAGE_BASE;var REMOTE_PACKAGE_SIZE=metadata.remote_package_size;var PACKAGE_UUID=metadata.package_uuid;function fetchRemotePackage(packageName,packageSize,callback,errback){var xhr=new XMLHttpRequest;xhr.open("GET",packageName,true);xhr.responseType="arraybuffer";xhr.onprogress=function(event){var url=packageName;var size=packageSize;if(event.total)size=event.total;if(event.loaded){if(!xhr.addedTotal){xhr.addedTotal=true;if(!Module.dataFileDownloads)Module.dataFileDownloads={};Module.dataFileDownloads[url]={loaded:event.loaded,total:size}}else{Module.dataFileDownloads[url].loaded=event.loaded}var total=0;var loaded=0;var num=0;for(var download in Module.dataFileDownloads){var data=Module.dataFileDownloads[download];total+=data.total;loaded+=data.loaded;num++}total=Math.ceil(total*Module.expectedDataFileDownloads/num);if(Module["setStatus"])Module["setStatus"]("Downloading data... ("+loaded+"/"+total+")")}else if(!Module.dataFileDownloads){if(Module["setStatus"])Module["setStatus"]("Downloading data...")}};xhr.onerror=function(event){throw new Error("NetworkError for: "+packageName)};xhr.onload=function(event){if(xhr.status==200||xhr.status==304||xhr.status==206||xhr.status==0&&xhr.response){var packageData=xhr.response;callback(packageData)}else{throw new Error(xhr.statusText+" : "+xhr.responseURL)}};xhr.send(null)}function handleError(error){console.error("package error:",error)}var fetchedCallback=null;var fetched=Module["getPreloadedPackage"]?Module["getPreloadedPackage"](REMOTE_PACKAGE_NAME,REMOTE_PACKAGE_SIZE):null;if(!fetched)fetchRemotePackage(REMOTE_PACKAGE_NAME,REMOTE_PACKAGE_SIZE,function(data){if(fetchedCallback){fetchedCallback(data);fetchedCallback=null}else{fetched=data}},handleError);function runWithFS(){function assert(check,msg){if(!check)throw msg+(new Error).stack}Module["FS_createPath"]("/","lib",true,true);Module["FS_createPath"]("/lib","python3.8",true,true);Module["FS_createPath"]("/lib/python3.8","site-packages",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages","html5lib",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages/html5lib","filters",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages/html5lib","treebuilders",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages/html5lib","treewalkers",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages/html5lib","_trie",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages/html5lib","treeadapters",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages","html5lib-1.1-py3.8.egg-info",true,true);function DataRequest(start,end,audio){this.start=start;this.end=end;this.audio=audio}DataRequest.prototype={requests:{},open:function(mode,name){this.name=name;this.requests[name]=this;Module["addRunDependency"]("fp "+this.name)},send:function(){},onload:function(){var byteArray=this.byteArray.subarray(this.start,this.end);this.finish(byteArray)},finish:function(byteArray){var that=this;Module["FS_createPreloadedFile"](this.name,null,byteArray,true,true,function(){Module["removeRunDependency"]("fp "+that.name)},function(){if(that.audio){Module["removeRunDependency"]("fp "+that.name)}else{err("Preloading file "+that.name+" failed")}},false,true);this.requests[this.name]=null}};function processPackageData(arrayBuffer){Module.finishedDataFileDownloads++;assert(arrayBuffer,"Loading data file failed.");assert(arrayBuffer instanceof ArrayBuffer,"bad input to processPackageData");var byteArray=new Uint8Array(arrayBuffer);var curr;var compressedData={data:null,cachedOffset:235658,cachedIndexes:[-1,-1],cachedChunks:[null,null],offsets:[0,1267,2606,3944,5242,6706,8249,9372,10289,11562,12800,13928,15163,16181,17123,17934,19092,20039,20789,21608,22318,23e3,23656,24471,25070,25902,26980,28067,29173,30223,31109,32090,32967,33843,34760,35657,36592,37513,38448,39299,40218,41161,42086,42976,43905,44814,45719,46635,47419,48308,49248,50195,51140,52010,52914,53837,54711,55911,57186,58169,59513,60663,61791,62970,64311,65307,66213,67367,68196,69283,70228,71289,72181,73436,74617,75714,76786,77524,78576,79693,80776,82e3,83201,83803,84358,85079,85880,86899,87873,88743,89700,90733,91736,92613,93432,94059,94839,95707,96540,97405,98318,99046,100108,101026,101889,102700,103679,104723,105857,106698,107654,108631,109517,110412,111293,112291,112899,113973,114902,115818,116821,117523,118387,119321,120210,121114,122014,122820,123595,124366,125545,126867,127707,128889,129878,130961,131770,132431,133181,133866,134649,135279,135952,136496,136982,137654,138350,138817,139426,140198,141148,141848,142463,143167,143930,144829,145295,145817,146457,147049,147840,148652,149155,149775,150313,150837,151319,152156,153408,154780,155952,157036,157484,157992,158721,159459,160165,160930,161787,162838,163691,164830,165971,167105,168253,168988,170228,171267,172210,172973,173816,174547,175619,176689,177961,178818,179772,180740,181609,182701,183785,185221,186436,187547,188659,189769,190810,191903,192874,194081,195060,195944,196832,197772,198739,199681,200622,201513,202466,203329,204435,205343,206449,207702,208851,209828,210930,212067,212976,213910,214718,215970,216808,217851,218897,220096,221238,222387,223384,224710,225963,227267,228619,229874,231198,232564,233461,234465,235043,235388],sizes:[1267,1339,1338,1298,1464,1543,1123,917,1273,1238,1128,1235,1018,942,811,1158,947,750,819,710,682,656,815,599,832,1078,1087,1106,1050,886,981,877,876,917,897,935,921,935,851,919,943,925,890,929,909,905,916,784,889,940,947,945,870,904,923,874,1200,1275,983,1344,1150,1128,1179,1341,996,906,1154,829,1087,945,1061,892,1255,1181,1097,1072,738,1052,1117,1083,1224,1201,602,555,721,801,1019,974,870,957,1033,1003,877,819,627,780,868,833,865,913,728,1062,918,863,811,979,1044,1134,841,956,977,886,895,881,998,608,1074,929,916,1003,702,864,934,889,904,900,806,775,771,1179,1322,840,1182,989,1083,809,661,750,685,783,630,673,544,486,672,696,467,609,772,950,700,615,704,763,899,466,522,640,592,791,812,503,620,538,524,482,837,1252,1372,1172,1084,448,508,729,738,706,765,857,1051,853,1139,1141,1134,1148,735,1240,1039,943,763,843,731,1072,1070,1272,857,954,968,869,1092,1084,1436,1215,1111,1112,1110,1041,1093,971,1207,979,884,888,940,967,942,941,891,953,863,1106,908,1106,1253,1149,977,1102,1137,909,934,808,1252,838,1043,1046,1199,1142,1149,997,1326,1253,1304,1352,1255,1324,1366,897,1004,578,345,270],successes:[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]};compressedData.data=byteArray;assert(typeof Module.LZ4==="object","LZ4 not present - was your app build with  -s LZ4=1  ?");Module.LZ4.loadPackage({metadata:metadata,compressedData:compressedData});Module["removeRunDependency"]("datafile_html5lib.data")}Module["addRunDependency"]("datafile_html5lib.data");if(!Module.preloadResults)Module.preloadResults={};Module.preloadResults[PACKAGE_NAME]={fromCache:false};if(fetched){processPackageData(fetched);fetched=null}else{fetchedCallback=processPackageData}}if(Module["calledRun"]){runWithFS()}else{if(!Module["preRun"])Module["preRun"]=[];Module["preRun"].push(runWithFS)}};loadPackage({files:[{filename:"/lib/python3.8/site-packages/html5lib/_ihatexml.py",start:0,end:16728,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/serializer.py",start:16728,end:32475,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/constants.py",start:32475,end:115939,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/_inputstream.py",start:115939,end:148239,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/html5parser.py",start:148239,end:265413,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/_tokenizer.py",start:265413,end:342441,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/__init__.py",start:342441,end:343584,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/_utils.py",start:343584,end:348503,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/filters/sanitizer.py",start:348503,end:375388,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/filters/lint.py",start:375388,end:379019,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/filters/whitespace.py",start:379019,end:380233,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/filters/alphabeticalattributes.py",start:380233,end:381152,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/filters/optionaltags.py",start:381152,end:391740,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/filters/inject_meta_charset.py",start:391740,end:394685,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/filters/__init__.py",start:394685,end:394685,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/filters/base.py",start:394685,end:394971,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treebuilders/etree_lxml.py",start:394971,end:409725,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treebuilders/__init__.py",start:409725,end:413317,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treebuilders/base.py",start:413317,end:427870,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treebuilders/etree.py",start:427870,end:440694,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treebuilders/dom.py",start:440694,end:449619,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treewalkers/etree_lxml.py",start:449619,end:455964,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treewalkers/__init__.py",start:455964,end:461683,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treewalkers/genshi.py",start:461683,end:463992,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treewalkers/base.py",start:463992,end:471468,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treewalkers/etree.py",start:471468,end:476007,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treewalkers/dom.py",start:476007,end:477420,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/_trie/py.py",start:477420,end:479183,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/_trie/_base.py",start:479183,end:480196,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/_trie/__init__.py",start:480196,end:480305,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treeadapters/sax.py",start:480305,end:482081,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treeadapters/__init__.py",start:482081,end:482731,audio:0},{filename:"/lib/python3.8/site-packages/html5lib/treeadapters/genshi.py",start:482731,end:484446,audio:0},{filename:"/lib/python3.8/site-packages/html5lib-1.1-py3.8.egg-info/top_level.txt",start:484446,end:484455,audio:0},{filename:"/lib/python3.8/site-packages/html5lib-1.1-py3.8.egg-info/PKG-INFO",start:484455,end:504219,audio:0},{filename:"/lib/python3.8/site-packages/html5lib-1.1-py3.8.egg-info/requires.txt",start:504219,end:504422,audio:0},{filename:"/lib/python3.8/site-packages/html5lib-1.1-py3.8.egg-info/SOURCES.txt",start:504422,end:510895,audio:0},{filename:"/lib/python3.8/site-packages/html5lib-1.1-py3.8.egg-info/dependency_links.txt",start:510895,end:510896,audio:0}],remote_package_size:239754,package_uuid:"2ea70de4-aa05-4622-8a70-e50c65574656"})})();