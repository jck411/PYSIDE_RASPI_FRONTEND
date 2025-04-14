// ComponentCreator.js - Safe component creation utility

/**
 * Safely creates a QML component with properties
 *
 * @param {string} componentPath - Path to the QML component file
 * @param {object} parent - Parent object for the new component
 * @param {object} properties - Object containing properties to set
 * @return {object} The created component instance
 */
var createComponent = function(componentPath, parent, properties) {
    console.log("ComponentCreator: Creating component", componentPath);
    
    // Create the component
    var component = Qt.createComponent(componentPath);
    
    // Check if component was created successfully
    if (component.status === Component.Ready) {
        console.log("ComponentCreator: Component ready");
        
        // Create object without properties first
        var object = component.createObject(parent);
        
        if (object) {
            console.log("ComponentCreator: Object created successfully");
            
            // Set properties individually after object creation
            if (properties) {
                for (var key in properties) {
                    if (properties.hasOwnProperty(key)) {
                        console.log("ComponentCreator: Setting property", key);
                        object[key] = properties[key];
                    }
                }
            }
            
            return object;
        } else {
            console.error("ComponentCreator: Error creating object:", component.errorString());
            return null;
        }
    } else if (component.status === Component.Loading) {
        console.log("ComponentCreator: Component is still loading");
        return null;
    } else {
        console.error("ComponentCreator: Error creating component:", component.errorString());
        return null;
    }
}; 