var Module=typeof pyodide._module!=="undefined"?pyodide._module:{};Module.checkABI(1);if(!Module.expectedDataFileDownloads){Module.expectedDataFileDownloads=0;Module.finishedDataFileDownloads=0}Module.expectedDataFileDownloads++;(function(){var loadPackage=function(metadata){var PACKAGE_PATH;if(typeof window==="object"){PACKAGE_PATH=window["encodeURIComponent"](window.location.pathname.toString().substring(0,window.location.pathname.toString().lastIndexOf("/"))+"/")}else if(typeof location!=="undefined"){PACKAGE_PATH=encodeURIComponent(location.pathname.toString().substring(0,location.pathname.toString().lastIndexOf("/"))+"/")}else{throw"using preloaded data can only be done on a web page or in a web worker"}var PACKAGE_NAME="toolz.data";var REMOTE_PACKAGE_BASE="toolz.data";if(typeof Module["locateFilePackage"]==="function"&&!Module["locateFile"]){Module["locateFile"]=Module["locateFilePackage"];err("warning: you defined Module.locateFilePackage, that has been renamed to Module.locateFile (using your locateFilePackage for now)")}var REMOTE_PACKAGE_NAME=Module["locateFile"]?Module["locateFile"](REMOTE_PACKAGE_BASE,""):REMOTE_PACKAGE_BASE;var REMOTE_PACKAGE_SIZE=metadata.remote_package_size;var PACKAGE_UUID=metadata.package_uuid;function fetchRemotePackage(packageName,packageSize,callback,errback){var xhr=new XMLHttpRequest;xhr.open("GET",packageName,true);xhr.responseType="arraybuffer";xhr.onprogress=function(event){var url=packageName;var size=packageSize;if(event.total)size=event.total;if(event.loaded){if(!xhr.addedTotal){xhr.addedTotal=true;if(!Module.dataFileDownloads)Module.dataFileDownloads={};Module.dataFileDownloads[url]={loaded:event.loaded,total:size}}else{Module.dataFileDownloads[url].loaded=event.loaded}var total=0;var loaded=0;var num=0;for(var download in Module.dataFileDownloads){var data=Module.dataFileDownloads[download];total+=data.total;loaded+=data.loaded;num++}total=Math.ceil(total*Module.expectedDataFileDownloads/num);if(Module["setStatus"])Module["setStatus"]("Downloading data... ("+loaded+"/"+total+")")}else if(!Module.dataFileDownloads){if(Module["setStatus"])Module["setStatus"]("Downloading data...")}};xhr.onerror=function(event){throw new Error("NetworkError for: "+packageName)};xhr.onload=function(event){if(xhr.status==200||xhr.status==304||xhr.status==206||xhr.status==0&&xhr.response){var packageData=xhr.response;callback(packageData)}else{throw new Error(xhr.statusText+" : "+xhr.responseURL)}};xhr.send(null)}function handleError(error){console.error("package error:",error)}var fetchedCallback=null;var fetched=Module["getPreloadedPackage"]?Module["getPreloadedPackage"](REMOTE_PACKAGE_NAME,REMOTE_PACKAGE_SIZE):null;if(!fetched)fetchRemotePackage(REMOTE_PACKAGE_NAME,REMOTE_PACKAGE_SIZE,function(data){if(fetchedCallback){fetchedCallback(data);fetchedCallback=null}else{fetched=data}},handleError);function runWithFS(){function assert(check,msg){if(!check)throw msg+(new Error).stack}Module["FS_createPath"]("/","lib",true,true);Module["FS_createPath"]("/lib","python3.8",true,true);Module["FS_createPath"]("/lib/python3.8","site-packages",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages","tlz",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages","toolz",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages/toolz","sandbox",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages/toolz","curried",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages/toolz","tests",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages","toolz-0.10.0-py3.8.egg-info",true,true);function DataRequest(start,end,audio){this.start=start;this.end=end;this.audio=audio}DataRequest.prototype={requests:{},open:function(mode,name){this.name=name;this.requests[name]=this;Module["addRunDependency"]("fp "+this.name)},send:function(){},onload:function(){var byteArray=this.byteArray.subarray(this.start,this.end);this.finish(byteArray)},finish:function(byteArray){var that=this;Module["FS_createPreloadedFile"](this.name,null,byteArray,true,true,function(){Module["removeRunDependency"]("fp "+that.name)},function(){if(that.audio){Module["removeRunDependency"]("fp "+that.name)}else{err("Preloading file "+that.name+" failed")}},false,true);this.requests[this.name]=null}};function processPackageData(arrayBuffer){Module.finishedDataFileDownloads++;assert(arrayBuffer,"Loading data file failed.");assert(arrayBuffer instanceof ArrayBuffer,"bad input to processPackageData");var byteArray=new Uint8Array(arrayBuffer);var curr;var compressedData={data:null,cachedOffset:99203,cachedIndexes:[-1,-1],cachedChunks:[null,null],offsets:[0,1063,2248,3439,4731,5683,6769,7758,9003,10302,11536,12737,14127,15325,16239,17578,18840,20261,21215,22298,23470,24397,25453,26837,27975,29027,30184,31525,32675,33585,34430,35348,36454,37411,38782,39714,40498,41462,42390,43031,43494,44062,45002,46178,46964,48160,49234,50177,51321,52578,54001,55395,56700,58205,59144,60200,61310,62539,63407,64265,65335,66318,67324,68167,68971,69975,70704,71687,72651,73793,74751,75692,76494,77560,78530,79654,80725,81847,82665,83387,84510,85502,86520,87289,88e3,88961,89505,90016,90801,91576,92267,93385,94431,95354,96457,97698,98734],sizes:[1063,1185,1191,1292,952,1086,989,1245,1299,1234,1201,1390,1198,914,1339,1262,1421,954,1083,1172,927,1056,1384,1138,1052,1157,1341,1150,910,845,918,1106,957,1371,932,784,964,928,641,463,568,940,1176,786,1196,1074,943,1144,1257,1423,1394,1305,1505,939,1056,1110,1229,868,858,1070,983,1006,843,804,1004,729,983,964,1142,958,941,802,1066,970,1124,1071,1122,818,722,1123,992,1018,769,711,961,544,511,785,775,691,1118,1046,923,1103,1241,1036,469],successes:[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]};compressedData.data=byteArray;assert(typeof Module.LZ4==="object","LZ4 not present - was your app build with  -s LZ4=1  ?");Module.LZ4.loadPackage({metadata:metadata,compressedData:compressedData});Module["removeRunDependency"]("datafile_toolz.data")}Module["addRunDependency"]("datafile_toolz.data");if(!Module.preloadResults)Module.preloadResults={};Module.preloadResults[PACKAGE_NAME]={fromCache:false};if(fetched){processPackageData(fetched);fetched=null}else{fetchedCallback=processPackageData}}if(Module["calledRun"]){runWithFS()}else{if(!Module["preRun"])Module["preRun"]=[];Module["preRun"].push(runWithFS)}};loadPackage({files:[{filename:"/lib/python3.8/site-packages/tlz/__init__.py",start:0,end:338,audio:0},{filename:"/lib/python3.8/site-packages/tlz/_build_tlz.py",start:338,end:3685,audio:0},{filename:"/lib/python3.8/site-packages/toolz/compatibility.py",start:3685,end:4842,audio:0},{filename:"/lib/python3.8/site-packages/toolz/utils.py",start:4842,end:4981,audio:0},{filename:"/lib/python3.8/site-packages/toolz/itertoolz.py",start:4981,end:32643,audio:0},{filename:"/lib/python3.8/site-packages/toolz/recipes.py",start:32643,end:33930,audio:0},{filename:"/lib/python3.8/site-packages/toolz/functoolz.py",start:33930,end:68435,audio:0},{filename:"/lib/python3.8/site-packages/toolz/_signatures.py",start:68435,end:90903,audio:0},{filename:"/lib/python3.8/site-packages/toolz/__init__.py",start:90903,end:91227,audio:0},{filename:"/lib/python3.8/site-packages/toolz/dicttoolz.py",start:91227,end:100226,audio:0},{filename:"/lib/python3.8/site-packages/toolz/sandbox/parallel.py",start:100226,end:103057,audio:0},{filename:"/lib/python3.8/site-packages/toolz/sandbox/core.py",start:103057,end:107393,audio:0},{filename:"/lib/python3.8/site-packages/toolz/sandbox/__init__.py",start:107393,end:107461,audio:0},{filename:"/lib/python3.8/site-packages/toolz/curried/operator.py",start:107461,end:107951,audio:0},{filename:"/lib/python3.8/site-packages/toolz/curried/__init__.py",start:107951,end:110651,audio:0},{filename:"/lib/python3.8/site-packages/toolz/curried/exceptions.py",start:110651,end:110988,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_utils.py",start:110988,end:111144,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_curried.py",start:111144,end:114791,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_curried_doctests.py",start:114791,end:115065,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_itertoolz.py",start:115065,end:133268,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_signatures.py",start:133268,end:136195,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_functoolz.py",start:136195,end:156532,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_recipes.py",start:156532,end:157352,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_dicttoolz.py",start:157352,end:166285,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_serialization.py",start:166285,end:172143,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_inspect_args.py",start:172143,end:188359,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_compatibility.py",start:188359,end:188904,audio:0},{filename:"/lib/python3.8/site-packages/toolz/tests/test_tlz.py",start:188904,end:190413,audio:0},{filename:"/lib/python3.8/site-packages/toolz-0.10.0-py3.8.egg-info/top_level.txt",start:190413,end:190423,audio:0},{filename:"/lib/python3.8/site-packages/toolz-0.10.0-py3.8.egg-info/PKG-INFO",start:190423,end:196637,audio:0},{filename:"/lib/python3.8/site-packages/toolz-0.10.0-py3.8.egg-info/not-zip-safe",start:196637,end:196638,audio:0},{filename:"/lib/python3.8/site-packages/toolz-0.10.0-py3.8.egg-info/SOURCES.txt",start:196638,end:197539,audio:0},{filename:"/lib/python3.8/site-packages/toolz-0.10.0-py3.8.egg-info/dependency_links.txt",start:197539,end:197540,audio:0}],remote_package_size:103299,package_uuid:"20e2bd7a-91ad-4d02-aab7-8cd408c58af0"})})();