var Module=typeof pyodide._module!=="undefined"?pyodide._module:{};Module.checkABI(1);if(!Module.expectedDataFileDownloads){Module.expectedDataFileDownloads=0;Module.finishedDataFileDownloads=0}Module.expectedDataFileDownloads++;(function(){var loadPackage=function(metadata){var PACKAGE_PATH;if(typeof window==="object"){PACKAGE_PATH=window["encodeURIComponent"](window.location.pathname.toString().substring(0,window.location.pathname.toString().lastIndexOf("/"))+"/")}else if(typeof location!=="undefined"){PACKAGE_PATH=encodeURIComponent(location.pathname.toString().substring(0,location.pathname.toString().lastIndexOf("/"))+"/")}else{throw"using preloaded data can only be done on a web page or in a web worker"}var PACKAGE_NAME="distlib.data";var REMOTE_PACKAGE_BASE="distlib.data";if(typeof Module["locateFilePackage"]==="function"&&!Module["locateFile"]){Module["locateFile"]=Module["locateFilePackage"];err("warning: you defined Module.locateFilePackage, that has been renamed to Module.locateFile (using your locateFilePackage for now)")}var REMOTE_PACKAGE_NAME=Module["locateFile"]?Module["locateFile"](REMOTE_PACKAGE_BASE,""):REMOTE_PACKAGE_BASE;var REMOTE_PACKAGE_SIZE=metadata.remote_package_size;var PACKAGE_UUID=metadata.package_uuid;function fetchRemotePackage(packageName,packageSize,callback,errback){var xhr=new XMLHttpRequest;xhr.open("GET",packageName,true);xhr.responseType="arraybuffer";xhr.onprogress=function(event){var url=packageName;var size=packageSize;if(event.total)size=event.total;if(event.loaded){if(!xhr.addedTotal){xhr.addedTotal=true;if(!Module.dataFileDownloads)Module.dataFileDownloads={};Module.dataFileDownloads[url]={loaded:event.loaded,total:size}}else{Module.dataFileDownloads[url].loaded=event.loaded}var total=0;var loaded=0;var num=0;for(var download in Module.dataFileDownloads){var data=Module.dataFileDownloads[download];total+=data.total;loaded+=data.loaded;num++}total=Math.ceil(total*Module.expectedDataFileDownloads/num);if(Module["setStatus"])Module["setStatus"]("Downloading data... ("+loaded+"/"+total+")")}else if(!Module.dataFileDownloads){if(Module["setStatus"])Module["setStatus"]("Downloading data...")}};xhr.onerror=function(event){throw new Error("NetworkError for: "+packageName)};xhr.onload=function(event){if(xhr.status==200||xhr.status==304||xhr.status==206||xhr.status==0&&xhr.response){var packageData=xhr.response;callback(packageData)}else{throw new Error(xhr.statusText+" : "+xhr.responseURL)}};xhr.send(null)}function handleError(error){console.error("package error:",error)}var fetchedCallback=null;var fetched=Module["getPreloadedPackage"]?Module["getPreloadedPackage"](REMOTE_PACKAGE_NAME,REMOTE_PACKAGE_SIZE):null;if(!fetched)fetchRemotePackage(REMOTE_PACKAGE_NAME,REMOTE_PACKAGE_SIZE,function(data){if(fetchedCallback){fetchedCallback(data);fetchedCallback=null}else{fetched=data}},handleError);function runWithFS(){function assert(check,msg){if(!check)throw msg+(new Error).stack}Module["FS_createPath"]("/","lib",true,true);Module["FS_createPath"]("/lib","python3.8",true,true);Module["FS_createPath"]("/lib/python3.8","site-packages",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages","distlib",true,true);Module["FS_createPath"]("/lib/python3.8/site-packages/distlib","_backport",true,true);function DataRequest(start,end,audio){this.start=start;this.end=end;this.audio=audio}DataRequest.prototype={requests:{},open:function(mode,name){this.name=name;this.requests[name]=this;Module["addRunDependency"]("fp "+this.name)},send:function(){},onload:function(){var byteArray=this.byteArray.subarray(this.start,this.end);this.finish(byteArray)},finish:function(byteArray){var that=this;Module["FS_createPreloadedFile"](this.name,null,byteArray,true,true,function(){Module["removeRunDependency"]("fp "+that.name)},function(){if(that.audio){Module["removeRunDependency"]("fp "+that.name)}else{err("Preloading file "+that.name+" failed")}},false,true);this.requests[this.name]=null}};function processPackageData(arrayBuffer){Module.finishedDataFileDownloads++;assert(arrayBuffer,"Loading data file failed.");assert(arrayBuffer instanceof ArrayBuffer,"bad input to processPackageData");var byteArray=new Uint8Array(arrayBuffer);var curr;var compressedData={data:null,cachedOffset:588575,cachedIndexes:[-1,-1],cachedChunks:[null,null],offsets:[0,1177,2451,3612,4641,5698,6893,8017,9208,10577,11759,12770,13654,14617,15510,16618,17598,18688,19974,21069,22205,23470,24822,25981,27226,28375,29622,30766,31638,32887,33996,35120,36401,37271,38206,39500,40785,41943,43005,44184,45199,46340,47622,48734,49793,50700,51718,52755,53888,54932,55952,57263,58342,59655,61440,63227,65118,66926,68815,70646,72473,74298,76069,77782,79481,81334,83235,85070,86903,88752,90542,92276,94122,95948,97668,99164,100860,102673,104403,106249,108028,109880,111499,112562,113770,114604,115616,117020,118545,119923,120565,121247,122124,123883,125165,126855,128363,129684,131150,132510,133683,134811,136329,137664,138547,139852,141621,143460,145279,147151,148979,150816,152627,154383,156228,158053,159822,161512,163353,165127,166929,168704,170302,172013,173727,175354,177156,179e3,180643,181886,183275,183819,185163,186442,187242,187840,188730,190470,192154,193418,194750,196159,197456,198344,199843,201083,202476,204526,204846,205975,207137,208365,209660,210752,211418,212580,213952,215145,216333,217545,219040,220238,221357,222242,223208,224398,225353,226699,228134,229331,230519,231826,232951,233980,235150,236396,237814,239180,240480,241716,242854,243783,244968,246046,247215,248312,249643,251035,252246,253439,254666,255749,256984,257929,259088,260144,261321,262305,263456,264663,265724,266808,268275,270051,271936,273733,275613,277481,279091,280920,282577,284411,286141,288013,289832,291428,293166,294899,296748,298552,300315,301913,303599,305419,307042,308621,310365,312251,313724,315286,316415,316904,318201,319431,320241,321105,321731,323465,325154,326414,327758,329173,330471,331343,332857,334115,335487,337542,337952,339178,340510,341838,343123,344380,345538,346802,347791,348850,350090,351061,352417,353447,354470,355484,356672,357492,358349,359308,360313,361571,363355,365115,366975,368795,370692,372533,374320,376041,377917,379651,381565,383352,385224,387058,388868,390620,392434,394140,395883,397376,399243,401101,402783,404562,406402,408080,409318,410383,411260,412339,413760,415255,416646,417319,417846,418849,420582,421833,423523,425050,426351,427835,429213,430350,431497,433009,434339,435234,436584,437404,438467,439366,440524,441884,443042,444379,445447,446614,447647,448833,450034,451393,452709,454063,455077,456120,457274,458468,459731,460708,461932,462987,464277,465159,466433,467566,468713,470094,471318,472253,473428,474636,475855,476858,477998,479229,480457,481693,482783,483985,485208,486465,487737,488927,489875,491091,492163,493366,494454,495557,496824,497807,499119,500302,501286,502319,503434,504669,505922,507121,508461,509392,510590,511809,513056,514343,515377,516774,518131,519169,520484,521737,522985,524256,525471,526789,528022,529332,530556,531852,533151,534407,535590,537219,538381,539427,540681,541949,543007,544201,545322,546423,547448,548566,549697,550816,551769,552961,554037,555138,556193,557452,558667,559912,561066,562256,563502,564513,565554,566757,567891,569019,570097,571061,572101,573306,574423,575455,576577,577809,578935,580146,581176,582253,583122,584062,585248,586474,587616,588441],sizes:[1177,1274,1161,1029,1057,1195,1124,1191,1369,1182,1011,884,963,893,1108,980,1090,1286,1095,1136,1265,1352,1159,1245,1149,1247,1144,872,1249,1109,1124,1281,870,935,1294,1285,1158,1062,1179,1015,1141,1282,1112,1059,907,1018,1037,1133,1044,1020,1311,1079,1313,1785,1787,1891,1808,1889,1831,1827,1825,1771,1713,1699,1853,1901,1835,1833,1849,1790,1734,1846,1826,1720,1496,1696,1813,1730,1846,1779,1852,1619,1063,1208,834,1012,1404,1525,1378,642,682,877,1759,1282,1690,1508,1321,1466,1360,1173,1128,1518,1335,883,1305,1769,1839,1819,1872,1828,1837,1811,1756,1845,1825,1769,1690,1841,1774,1802,1775,1598,1711,1714,1627,1802,1844,1643,1243,1389,544,1344,1279,800,598,890,1740,1684,1264,1332,1409,1297,888,1499,1240,1393,2050,320,1129,1162,1228,1295,1092,666,1162,1372,1193,1188,1212,1495,1198,1119,885,966,1190,955,1346,1435,1197,1188,1307,1125,1029,1170,1246,1418,1366,1300,1236,1138,929,1185,1078,1169,1097,1331,1392,1211,1193,1227,1083,1235,945,1159,1056,1177,984,1151,1207,1061,1084,1467,1776,1885,1797,1880,1868,1610,1829,1657,1834,1730,1872,1819,1596,1738,1733,1849,1804,1763,1598,1686,1820,1623,1579,1744,1886,1473,1562,1129,489,1297,1230,810,864,626,1734,1689,1260,1344,1415,1298,872,1514,1258,1372,2055,410,1226,1332,1328,1285,1257,1158,1264,989,1059,1240,971,1356,1030,1023,1014,1188,820,857,959,1005,1258,1784,1760,1860,1820,1897,1841,1787,1721,1876,1734,1914,1787,1872,1834,1810,1752,1814,1706,1743,1493,1867,1858,1682,1779,1840,1678,1238,1065,877,1079,1421,1495,1391,673,527,1003,1733,1251,1690,1527,1301,1484,1378,1137,1147,1512,1330,895,1350,820,1063,899,1158,1360,1158,1337,1068,1167,1033,1186,1201,1359,1316,1354,1014,1043,1154,1194,1263,977,1224,1055,1290,882,1274,1133,1147,1381,1224,935,1175,1208,1219,1003,1140,1231,1228,1236,1090,1202,1223,1257,1272,1190,948,1216,1072,1203,1088,1103,1267,983,1312,1183,984,1033,1115,1235,1253,1199,1340,931,1198,1219,1247,1287,1034,1397,1357,1038,1315,1253,1248,1271,1215,1318,1233,1310,1224,1296,1299,1256,1183,1629,1162,1046,1254,1268,1058,1194,1121,1101,1025,1118,1131,1119,953,1192,1076,1101,1055,1259,1215,1245,1154,1190,1246,1011,1041,1203,1134,1128,1078,964,1040,1205,1117,1032,1122,1232,1126,1211,1030,1077,869,940,1186,1226,1142,825,134],successes:[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]};compressedData.data=byteArray;assert(typeof Module.LZ4==="object","LZ4 not present - was your app build with  -s LZ4=1  ?");Module.LZ4.loadPackage({metadata:metadata,compressedData:compressedData});Module["removeRunDependency"]("datafile_distlib.data")}Module["addRunDependency"]("datafile_distlib.data");if(!Module.preloadResults)Module.preloadResults={};Module.preloadResults[PACKAGE_NAME]={fromCache:false};if(fetched){processPackageData(fetched);fetched=null}else{fetchedCallback=processPackageData}}if(Module["calledRun"]){runWithFS()}else{if(!Module["preRun"])Module["preRun"]=[];Module["preRun"].push(runWithFS)}};loadPackage({files:[{filename:"/lib/python3.8/site-packages/distlib-0.3.1-py3.8.egg-info",start:0,end:1261,audio:0},{filename:"/lib/python3.8/site-packages/distlib/wheel.py",start:1261,end:42405,audio:0},{filename:"/lib/python3.8/site-packages/distlib/index.py",start:42405,end:63471,audio:0},{filename:"/lib/python3.8/site-packages/distlib/metadata.py",start:63471,end:102433,audio:0},{filename:"/lib/python3.8/site-packages/distlib/markers.py",start:102433,end:106820,audio:0},{filename:"/lib/python3.8/site-packages/distlib/t64.exe",start:106820,end:212804,audio:0},{filename:"/lib/python3.8/site-packages/distlib/w32.exe",start:212804,end:302916,audio:0},{filename:"/lib/python3.8/site-packages/distlib/version.py",start:302916,end:326307,audio:0},{filename:"/lib/python3.8/site-packages/distlib/manifest.py",start:326307,end:341118,audio:0},{filename:"/lib/python3.8/site-packages/distlib/__init__.py",start:341118,end:341699,audio:0},{filename:"/lib/python3.8/site-packages/distlib/scripts.py",start:341699,end:358879,audio:0},{filename:"/lib/python3.8/site-packages/distlib/locators.py",start:358879,end:410979,audio:0},{filename:"/lib/python3.8/site-packages/distlib/t32.exe",start:410979,end:507747,audio:0},{filename:"/lib/python3.8/site-packages/distlib/compat.py",start:507747,end:549155,audio:0},{filename:"/lib/python3.8/site-packages/distlib/w64.exe",start:549155,end:648995,audio:0},{filename:"/lib/python3.8/site-packages/distlib/util.py",start:648995,end:708840,audio:0},{filename:"/lib/python3.8/site-packages/distlib/database.py",start:708840,end:759899,audio:0},{filename:"/lib/python3.8/site-packages/distlib/resources.py",start:759899,end:770665,audio:0},{filename:"/lib/python3.8/site-packages/distlib/_backport/sysconfig.py",start:770665,end:797519,audio:0},{filename:"/lib/python3.8/site-packages/distlib/_backport/shutil.py",start:797519,end:823226,audio:0},{filename:"/lib/python3.8/site-packages/distlib/_backport/tarfile.py",start:823226,end:915854,audio:0},{filename:"/lib/python3.8/site-packages/distlib/_backport/__init__.py",start:915854,end:916128,audio:0},{filename:"/lib/python3.8/site-packages/distlib/_backport/sysconfig.cfg",start:916128,end:918745,audio:0},{filename:"/lib/python3.8/site-packages/distlib/_backport/misc.py",start:918745,end:919716,audio:0}],remote_package_size:592671,package_uuid:"09499400-8992-4d8d-b597-c7a5e23311bc"})})();