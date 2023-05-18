
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
 *      Edit fcts
 */

function osais_ai_onEditChange(_idEdit, _idInForm) {
    let _eltEdit = document.getElementById(_idEdit);
    let _eltInForm = document.getElementById(_idInForm);
    _eltInForm.value=_eltEdit.value;
}

/* 
 *      Range Slider fcts
 */

function osais_ai_onRangeSliderChange(_idSlider, _idInForm, _idValue, _displayAsPercent, _min, _max) {
    let _eltSlider = document.getElementById(_idSlider);
    let _eltInForm = document.getElementById(_idInForm);
    let _eltValue = document.getElementById(_idValue);
    _eltValue.innerHTML=_eltSlider.value;
    let _rebased=parseFloat(_eltSlider.value);
    if(_displayAsPercent) {
        _min=parseFloat(_min);
        _max=parseFloat(_max);
        _rebased= _min+ (parseFloat(_eltSlider.value)/100) * (_max-_min);
    }
    _eltInForm.value=_rebased;
}

/* 
 *      Multi Toggle fcts
 */

function osais_ai_onMultiToggleUpdate(_id, _idInForm, _prop, _val) {
    let _myObj = document.getElementById(_id);
    let _eltInForm = document.getElementById(_idInForm);
    let _myProp = document.getElementById(_prop);
    _myObj.classList.add('active');
    _myProp.value=_val;

    _eltInForm.value=_val;
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

function osais_ai_onSelectFile(event, eltSelPict, eltInForm) {
    let _myObj = document.getElementById(eltSelPict);
    let _myInput = document.getElementById(eltInForm);      // eg "url_upload"

    let _resetFile=function(_myObj){
        // remove prev image
        _myObj.classList.add("before");
        _myObj.classList.remove("after");
        _myInput.value=null;
        osais_ai_validateForm();
    }

    if(event===null) {
        _resetFile(_myObj);
        return false;
    }

    // get this image
    event.preventDefault();
    let selFile=null;
    if(event.target.files.length!==0) {
        selFile=event.target.files[0];
        if(!selFile) {
            _resetFile(_myObj);
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
                _resetFile(_myObj);
                return false;                    
            }

            _myObj.classList.remove("before");
            _myObj.classList.add("after");
            _myInput.value=selFile.name;

            // store this image on server, so that we have it ready for processing
            osais_ai_postFile(selFile)
            .then(dataS3 => {
                if(_myInput && dataS3 && dataS3.data) {
                    try {
                        let _s3=dataS3.data[selFile.name];
                        _myInput.value=_s3;
                    }
                    catch(err){}
                }
            })
            .catch(err=> {

            })

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
async function osais_ai_postRequest(_name) {
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
            _data[key]=myForm[i].value;
        }

        // show processing modal...
        osais_ai_showModal()

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
        osais_ai_showModalLink(_name, json.data.uid);

        return false;
    } catch(error) {
        console.log(error);
        return false;
    }
}

function _showModal(stage, objParam) {
    let _modalBackground = document.getElementById("idBackground");
    let _modalPreviewImage = document.getElementById("idModalPreviewImage");        
    let _myImg = document.getElementById("idUploadImage");
    let _modal = document.getElementById("idModal");

    switch(stage) {
        // hide
        case 0:
            _modalBackground.classList.remove('active');
            _modal.classList.remove('active');    
            _modal.classList.remove('before');    
            _modal.classList.remove('after');    
            break;

        // in progress
        case 1:
            _modalPreviewImage.src=_myImg.src;
            _modalBackground.classList.add('active');
            _modal.classList.add('active');    
            _modal.classList.add('before');    
            break;

        // show link to result
        case 2:
            _modal.classList.remove('before');    
            _modal.classList.add('after');    
            let _href = document.getElementById("idRef");
            _href.href="https://opensourceais.com/WorldOfAIs/ai/"+objParam.name+"/"+objParam.uid
            break;
    }
}

function osais_ai_showModalLink(_name, _uid) {
    _showModal(2, {
        name: _name,
        uid: _uid
    });
}

function osais_ai_showModal() {
    _showModal(1, null);
}

function osais_ai_hideModal() {
    _showModal(0);
}
