
/* 
 *      Form validation fcts
 */

function osais_ai_validateObject (_object) {
    let _obj=document.getElementById(_object.in);
    if(!_obj) {
        return false;
    }

    // reset value to bool
    if (_object.type=="boolean") {
        if(_obj.value==="False") {
            _obj.value=false
        }
        if(_obj.value==="True") {
            _obj.value=true
        }
    }

    // change to JS null
    if (_obj.value==="null") {
        _obj.value=null;
    } 
                
    // change to int
    if (_object.type=="int") {
        _obj.value=parseInt(_obj.value);
    } 
                
    // change to float
    if (_object.type=="int") {
        _obj.value=parseFloat(_obj.value);
    } 

    // check value of a mandatory field 
    if(_object.isMandatory==="true" || _object.isMandatory===true)  {
        if(_obj.value===undefined || _obj.value===null || _obj.value==="") {
            return false;
        }
    }

    // autofill
    if (_object.ui && _object.ui.autofill) {
        for (var j=0; j<_object.ui.autofill.length; j++ ){
            let _objAuto=document.getElementById(_object.ui.autofill[j].in);
            if(_objAuto) {
                _objAuto.value=_obj.value;
            }
        }
    } 

    return true;
}

function osais_ai_validateForm( ) {
    let bIsValid=true;
    
    // validate all objects
    if(osais_ai_validateAllObjects) {
        bIsValid=osais_ai_validateAllObjects();
    }

    const mySubmit = document.getElementById("submit");
    if(bIsValid) {
        mySubmit.classList.remove('disabled');
    }
    else {
        mySubmit.classList.add('disabled');
        return false;
    }
    return true;
}


/* 
 *      Multi Toggle fcts
 */

function osais_ai_onMultiToggleUpdate(_id, _prop, _val) {
    let _myObj = document.getElementById(_id);
    let _myProp = document.getElementById(_prop);
    _myObj.classList.add('active');
    _myProp.value=_val;

    osais_ai_validateForm();
}

function osais_ai_onMultiToggleReset(_base, _opt) {
    for (var i=0; i<_opt.length ; i++) {
        let _myObj = document.getElementById(_base+"_"+_opt[i]);
        if(_myObj) {
            _myObj.classList.remove('active');
        }                        
    }
}

/* 
 *      select Picture fcts
 */

function osais_ai_onSelectFile(event) {
    let _myObj = document.getElementById("selectPicture");
    let _myInput = document.getElementById("url_upload");

    let _resetFile=function(){
        // remove prev image
        _myObj.classList.add("before");
        _myObj.classList.remove("after");
        _myInput.value=null;
        osais_ai_validateForm();
    }

    if(event===null) {
        _resetFile();
        return false;
    }

    // get this image
    event.preventDefault();
    let selFile=null;
    if(event.target.files.length!==0) {
        selFile=event.target.files[0];
        if(!selFile) {
            _resetFile();
            return false;
        }
    }

    const reader = new FileReader();
    reader.readAsDataURL(selFile);
    let _myImg = document.getElementById("idUploadImage");

    // async here...
    reader.onload = (e) => {
        _myImg.src = e.target.result;
        if(_myImg.src) {
        
            // do not take anything else than PNG/JPEG
            if(selFile.type!== "image/png" && selFile.type!== "image/jpeg") {
                _resetFile();
                return false;                    
            }

            _myObj.classList.remove("before");
            _myObj.classList.add("after");
            _myInput.value=selFile.name;

            // store this image on server, so that we have it ready for processing
            osais_ai_postFile(selFile);

            osais_ai_validateForm();
            return true;
        }
    }    
};

/* 
 *      Post Request to OSAIS
 */

let gAuthToken=null;
let gRoute=null;

function osais_ai_setAuthToken(_token) {
    gAuthToken=_token;
}

function osais_ai_setOSAISRoute(_route) {
    gRoute=_route;
}

async function osais_ai_postFile(file){
    const formData = new FormData()
    formData.append('file', file)
    let response=await axios({
        method: 'post',
        url: '/upload',
        data: formData,
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'multipart/form-data'
        },
    });
    return response;
}

// we use this as a form validation, will always return false, but will send request if possible.
async function osais_ai_postRequest() {
    try {
        // first validate data
        if(!osais_ai_validateForm( )) {
            return;
        }

        // get data
        const myForm = document.getElementById("formRun");
        let _data={};
        for (var i=0 ; i<myForm.length; i++) {
            var key = myForm[i].id;

            // special case of url_upload => we replace it by filename since we have uploaded it already
            if(key==="url_upload") {
                _data["filename"]=myForm[i].value;
            }
            else {
                _data[key]=myForm[i].value;
            }
        }

        // call osais
        let jsonStr=_data? JSON.stringify(_data): null;
        let _query={
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                "Authorization": "Bearer " + (gAuthToken? gAuthToken : "")
            },
        }
        if(jsonStr) {
            _query.body=jsonStr;
        }

        const response = await fetch(gRoute, _query);
        const json = await response.json();

        // todo : redirect to OSAIS for result

        return false;
    } catch(error) {
        console.log(error);
        return false;
    }
}