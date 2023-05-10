
/* 
 *      Form validation fcts
 */

function osais_ai_validateObject (_object) {
    let _obj=document.getElementById(_object.out);
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
            let _objAuto=document.getElementById(_object.ui.autofill[j].out);
            if(_objAuto) {
                _objAuto.value=_obj.value;
            }
        }
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

    validateForm();
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

function onSelectFile(event) {
    let _myObj = document.getElementById("selectPicture");
    let _myInput = document.getElementById("url_upload");

    let _resetFile=function(){
        // remove prev image
        _myObj.classList.add("before");
        _myObj.classList.remove("after");
        _myInput.value=null;
        validateForm();
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
            _myInput.value=selFile;
            validateForm();
            return true;
        }
    }    
};

/* 
 *      Post Request to OSAIS
 */
